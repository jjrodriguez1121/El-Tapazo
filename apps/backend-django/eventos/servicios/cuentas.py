"""Grupos y cuentas: la mesa, y la persona con su pulsera.

La cadena es `Evento → GrupoEvento → ClienteEvento → PedidoEvento`. El grupo es
la mesa o la mancha; la cuenta es la persona. Cada pedido se ata a una persona
concreta y no al grupo, para que se sepa quién pidió qué aunque paguen entre
todos.
"""

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from clientes.selectores import obtener_cliente
from eventos.excepciones import (
    CuentaYaLiberada,
    GrupoCerrado,
    JornadaNoAbierta,
    PulseraYaAsignada,
)
from eventos.models import ClienteEvento, Evento, GrupoEvento
from eventos.repositorios import cuentas as repositorio
from eventos.repositorios import grupos as repositorio_de_grupos
from eventos.servicios.jornadas import obtener_jornada
from eventos.servicios.pulseras import exigir_pulsera_disponible
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def abrir_grupo(
    *,
    evento_id: int,
    negocio_id: int,
    abierto_por_id: int,
    nombre_referencia: str = "",
    mesa_zona: str = "",
) -> GrupoEvento:
    """Abre la mesa a la que se van a colgar las cuentas.

    Raises:
        NoEncontradoEnEsteNegocio, JornadaNoAbierta.
    """
    jornada = obtener_jornada(evento_id=evento_id, negocio_id=negocio_id)
    if jornada.estado != Evento.Estado.EN_CURSO:
        raise JornadaNoAbierta
    return repositorio_de_grupos.crear(
        negocio_id=negocio_id,
        evento_id=evento_id,
        nombre_referencia=nombre_referencia.strip(),
        mesa_zona=mesa_zona.strip(),
        abierto_por_id=abierto_por_id,
    )


@transaction.atomic
def cerrar_grupo(*, grupo_id: int, negocio_id: int, cerrado_por_id: int) -> GrupoEvento:
    """Cierra la mesa. Las cuentas que sigan abiertas se liberan con ella.

    Raises:
        NoEncontradoEnEsteNegocio, GrupoCerrado.
    """
    grupo = obtener_grupo(grupo_id=grupo_id, negocio_id=negocio_id)
    if not grupo.esta_abierto:
        raise GrupoCerrado

    ahora = timezone.now()
    repositorio.abiertas_de_un_grupo(grupo_id=grupo_id, negocio_id=negocio_id).update(
        liberada_en=ahora, liberada_por_id=cerrado_por_id, actualizado_en=ahora
    )
    grupo.estado = GrupoEvento.Estado.CERRADO
    grupo.cerrado_por_id = cerrado_por_id
    grupo.cerrado_en = ahora
    grupo.save(update_fields=["estado", "cerrado_por", "cerrado_en", "actualizado_en"])
    return grupo


@transaction.atomic
def abrir_cuenta(
    *,
    grupo_id: int,
    cliente_id: int,
    negocio_id: int,
    asignada_por_id: int,
    pulsera_id: int | None = None,
    limite_alerta: Decimal | None = None,
) -> ClienteEvento:
    """Abre la cuenta de una persona dentro de una mesa.

    **La pulsera es opcional**: una cuenta sin pulsera se lleva a mano, que es
    el caso de una licorería que no reparte chips.

    **Ser menor de edad no impide abrir la cuenta** (decisión 7). La respuesta
    trae `es_menor_de_edad` para que la pantalla lo pinte en rojo, pero quien
    decide si se le vende es la persona de la barra.

    Raises:
        NoEncontradoEnEsteNegocio: el grupo, el cliente o la pulsera no son de
            este negocio.
        GrupoCerrado, PulseraNoDisponible, PulseraYaAsignada.
    """
    grupo = obtener_grupo(grupo_id=grupo_id, negocio_id=negocio_id)
    if not grupo.esta_abierto:
        raise GrupoCerrado

    cliente = obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    if pulsera_id is not None:
        exigir_pulsera_disponible(pulsera_id=pulsera_id, negocio_id=negocio_id)
        if repositorio.hay_asignacion_activa(pulsera_id=pulsera_id):
            raise PulseraYaAsignada

    try:
        with transaction.atomic():
            return repositorio.crear(
                negocio_id=negocio_id,
                grupo_evento_id=grupo.id,
                cliente_id=cliente.id,
                pulsera_id=pulsera_id,
                limite_alerta=limite_alerta,
                asignada_por_id=asignada_por_id,
            )
    except IntegrityError as error:
        # La comprobación de arriba deja una rendija entre el SELECT y el
        # INSERT. Quien cierra de verdad es la restricción parcial
        # `pulsera_con_una_sola_asignacion_activa`; esto solo la traduce a un
        # mensaje que se entiende. El savepoint evita que el error aborte la
        # transacción externa.
        raise PulseraYaAsignada from error


@transaction.atomic
def liberar_cuenta(*, cuenta_id: int, negocio_id: int, liberada_por_id: int) -> ClienteEvento:
    """Cierra la cuenta y deja la pulsera libre para la siguiente persona.

    El "borrado" ocurre aquí, en la base de datos: **el chip no se toca ni se
    reescribe jamás**. La próxima vez que esa pulsera se le ponga a alguien
    será una fila nueva.

    Raises:
        NoEncontradoEnEsteNegocio, CuentaYaLiberada.
    """
    cuenta = repositorio.bloquear(cuenta_id=cuenta_id, negocio_id=negocio_id)
    if cuenta is None:
        raise NoEncontradoEnEsteNegocio
    # Se vuelve a comprobar **después del bloqueo**: entre la lectura y aquí
    # otro cajero pudo haberla cerrado.
    if cuenta.liberada_en is not None:
        raise CuentaYaLiberada

    cuenta.liberada_en = timezone.now()
    cuenta.liberada_por_id = liberada_por_id
    cuenta.save(update_fields=["liberada_en", "liberada_por", "actualizado_en"])
    return cuenta


def obtener_grupo(*, grupo_id: int, negocio_id: int) -> GrupoEvento:
    """Raises: NoEncontradoEnEsteNegocio."""
    grupo = repositorio_de_grupos.obtener_del_negocio(grupo_id=grupo_id, negocio_id=negocio_id)
    if grupo is None:
        raise NoEncontradoEnEsteNegocio
    return grupo


def obtener_cuenta(*, cuenta_id: int, negocio_id: int) -> ClienteEvento:
    """Raises: NoEncontradoEnEsteNegocio."""
    cuenta = repositorio.obtener_del_negocio(cuenta_id=cuenta_id, negocio_id=negocio_id)
    if cuenta is None:
        raise NoEncontradoEnEsteNegocio
    return cuenta

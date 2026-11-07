"""Abrir y cerrar la jornada de venta.

"Evento" es el nombre que le puso el diseño porque nació pensando en fiestas,
pero lo que representa es **un periodo de venta que se abre, acumula pedidos y
se cierra cuadrando la caja**. La fiesta del sábado es un evento; el martes de
una licorería que abre a diario también.

Lo que no puede pasar es que alguien tenga que crearlo a mano cada mañana: eso
lo resuelve `obtener_o_abrir_jornada`. El cajero solo ve "abrir caja" y "cerrar
caja".
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from eventos.excepciones import CuentasSinSaldar, JornadaNoAbierta
from eventos.models import Evento
from eventos.repositorios import cuentas as repositorio_de_cuentas
from eventos.repositorios import eventos as repositorio
from nucleo.excepciones import NoEncontradoEnEsteNegocio
from nucleo.utilidades.fechas import en_palabras


@transaction.atomic
def obtener_o_abrir_jornada(*, negocio_id: int, ubicacion_id: int) -> Evento:
    """La jornada en curso de esa ubicación; si no hay, la abre.

    La carrera se corta **por partida doble**:

    * Se bloquea la fila de `Ubicacion`. Es el recurso que se disputan las dos
      peticiones y nada más en el sistema lo bloquea, así que no estorba a
      ninguna otra operación: la segunda espera y al entrar ya encuentra la
      jornada abierta.
    * Y detrás, la restricción parcial
      `evento_una_sola_jornada_en_curso_por_ubicacion`, que protege **todos**
      los caminos —el admin de Django, un script, `psql`— y no solo el que pasa
      por este servicio. Su `IntegrityError` se captura en un savepoint y se
      relee.

    Raises:
        NoEncontradoEnEsteNegocio: esa ubicación no es de este negocio.
    """
    if repositorio.bloquear_ubicacion(ubicacion_id=ubicacion_id, negocio_id=negocio_id) is None:
        raise NoEncontradoEnEsteNegocio

    abierta = repositorio.en_curso_en(ubicacion_id=ubicacion_id, negocio_id=negocio_id)
    if abierta is not None:
        return abierta

    try:
        with transaction.atomic():
            return repositorio.crear_jornada(
                negocio_id=negocio_id,
                ubicacion_id=ubicacion_id,
                nombre=_nombre_de_hoy(),
                fecha_inicio=timezone.now(),
            )
    except IntegrityError:
        # Otro camino la abrió entre medias. No es un error: la queremos igual.
        pass

    jornada = repositorio.en_curso_en(ubicacion_id=ubicacion_id, negocio_id=negocio_id)
    if jornada is None:  # pragma: no cover - solo si la restricción cambiara
        raise NoEncontradoEnEsteNegocio
    return jornada


@transaction.atomic
def cerrar_jornada(*, evento_id: int, negocio_id: int) -> Evento:
    """Cuadra la caja y cierra el periodo de venta.

    **Se bloquea si quedan cuentas sin saldar** (decisión 9), y la lista va en
    los `detalles`: la pantalla tiene que poder decir cuáles en vez de obligar
    a buscarlas una por una.

    Raises:
        NoEncontradoEnEsteNegocio, JornadaNoAbierta, CuentasSinSaldar.
    """
    jornada = obtener_jornada(evento_id=evento_id, negocio_id=negocio_id)
    if jornada.estado != Evento.Estado.EN_CURSO:
        raise JornadaNoAbierta

    abiertas = list(
        repositorio_de_cuentas.abiertas_de_un_evento(evento_id=evento_id, negocio_id=negocio_id)
    )
    if abiertas:
        raise CuentasSinSaldar(
            cuentas=[
                {"cuenta_id": cuenta.id, "cliente": cuenta.cliente.nombre_completo}
                for cuenta in abiertas
            ]
        )

    jornada.estado = Evento.Estado.CERRADO
    jornada.fecha_fin = timezone.now()
    jornada.save(update_fields=["estado", "fecha_fin", "actualizado_en"])
    return jornada


def obtener_jornada(*, evento_id: int, negocio_id: int) -> Evento:
    """Raises: NoEncontradoEnEsteNegocio."""
    jornada = repositorio.obtener_del_negocio(evento_id=evento_id, negocio_id=negocio_id)
    if jornada is None:
        raise NoEncontradoEnEsteNegocio
    return jornada


def _nombre_de_hoy() -> str:
    """`Jornada del 8 de septiembre`.

    Sale de `timezone.localdate()` y **nunca de `date.today()`**: una barra que
    abre a las once de la noche partiría cada noche en dos jornadas mal
    nombradas.
    """
    return f"Jornada del {en_palabras(timezone.localdate())}"

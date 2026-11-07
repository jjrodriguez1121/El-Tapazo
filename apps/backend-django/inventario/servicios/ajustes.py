"""Los dos servicios que se parecen y no son lo mismo.

Confundirlos es el error más caro de este módulo, así que van juntos aquí con
la diferencia escrita:

| Servicio | Lo que no cuadra es… | ¿Crea movimiento? |
| --- | --- | --- |
| `ajustar_existencias` | **el estante**: se contó y hay menos | **Sí**, tipo `ajuste`, con motivo. Registra un faltante |
| `reconstruir_saldo_desde_kardex` | **el caché**: el kardex está bien | **No.** Inventar un ajuste falsearía la historia de la mercancía |
"""

import logging
from decimal import Decimal

from django.db import transaction

from inventario.dtos import LineaDeMovimientoDTO
from inventario.excepciones import CantidadInvalida, MotivoObligatorio
from inventario.models import Existencia, MovimientoInventario
from inventario.repositorios import existencias as repositorio
from inventario.repositorios import movimientos as repositorio_de_movimientos
from inventario.servicios.movimientos import aplicar_movimientos
from nucleo.excepciones import NoEncontradoEnEsteNegocio

logger = logging.getLogger(__name__)


@transaction.atomic
def ajustar_existencias(
    *,
    producto_id: int,
    ubicacion_id: int,
    negocio_id: int,
    cantidad_contada: Decimal,
    usuario_id: int,
    motivo: str,
) -> MovimientoInventario | None:
    """Cuadra el saldo con lo que de verdad hay en el estante.

    Recibe **la cantidad contada, no la diferencia**: quien hace el conteo
    cuenta cajas, no calcula restas, y pedirle la diferencia es pedirle que se
    equivoque. La resta la hace este servicio con la fila ya bloqueada, así que
    una venta que entre a mitad del conteo no se pierde.

    Devuelve `None` si el conteo coincide: un movimiento de cero no es un
    movimiento, y la base lo prohíbe.

    Raises:
        MotivoObligatorio: un ajuste sin motivo es lo que no puede pasar en la
            tabla donde se detecta un faltante.
        CantidadInvalida: la cantidad contada es negativa.
    """
    if not motivo or not motivo.strip():
        raise MotivoObligatorio
    if cantidad_contada < 0:
        raise CantidadInvalida("No se puede contar una cantidad negativa.")

    existencia = repositorio.bloquear(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )
    disponible = Decimal("0.00") if existencia is None else existencia.cantidad_disponible
    diferencia = cantidad_contada - disponible
    if diferencia == 0:
        return None

    movimientos = aplicar_movimientos(
        lineas=[
            LineaDeMovimientoDTO(
                producto_id=producto_id, ubicacion_id=ubicacion_id, cantidad=diferencia
            )
        ],
        tipo=MovimientoInventario.Tipo.AJUSTE,
        # Referencia vacía: es un ajuste manual, no la anulación de nada. Eso
        # es lo que lo distingue de una anulación, que sí lleva el id del
        # movimiento que deshace.
        referencia_tipo=MovimientoInventario.ReferenciaTipo.AJUSTE,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=motivo.strip(),
    )
    return movimientos[0]


@transaction.atomic
def reconstruir_saldo_desde_kardex(
    *, producto_id: int, ubicacion_id: int, negocio_id: int
) -> Existencia:
    """Reescribe el saldo cacheado con lo que dice el kardex. **No crea kardex.**

    Es la reparación de un caché desviado, no un ajuste de inventario:
    inventarse un movimiento aquí falsearía la historia de la mercancía, que es
    justo lo que el kardex existe para contar.

    Que haga falta llamarla **es un síntoma de un bug**, no una operación
    normal, y por eso deja un WARNING con los dos valores.

    Raises:
        NoEncontradoEnEsteNegocio: no hay saldo de ese producto en ese sitio.
    """
    existencia = repositorio.bloquear(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )
    if existencia is None:
        raise NoEncontradoEnEsteNegocio

    segun_kardex = repositorio_de_movimientos.saldo_segun_kardex(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )
    if segun_kardex == existencia.cantidad_disponible:
        return existencia

    logger.warning(
        "Saldo desviado del kardex · producto=%s ubicacion=%s negocio=%s cacheado=%s kardex=%s",
        producto_id,
        ubicacion_id,
        negocio_id,
        existencia.cantidad_disponible,
        segun_kardex,
    )
    repositorio.fijar_saldo(existencia_id=existencia.id, cantidad=segun_kardex)
    existencia.refresh_from_db()
    return existencia

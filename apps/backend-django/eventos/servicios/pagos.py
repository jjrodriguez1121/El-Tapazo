"""El cobro.

**Una cuenta del bar se salda con un solo pago que cubre el total** (decisión
3). No hay abonos, y es a propósito: los abonos son del canal mayorista, donde
una tienda a 30 días paga en varias veces.

Lo consumido lo suma la base de datos (`selectores/saldos.py`), nunca Python.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from eventos.dtos import ResultadoDeCobroDTO
from eventos.excepciones import (
    CuentaYaLiberada,
    GrupoCerrado,
    PagoNoCubreElConsumo,
    PedidoNoCancelable,
)
from eventos.models import GrupoEvento, PedidoEvento
from eventos.repositorios import cuentas as repositorio_de_cuentas
from eventos.repositorios import pagos as repositorio
from eventos.repositorios import pedidos as repositorio_de_pedidos
from eventos.selectores import saldos
from eventos.servicios.cuentas import obtener_grupo
from eventos.servicios.pedidos import obtener_pedido
from nucleo.excepciones import NoEncontradoEnEsteNegocio


@transaction.atomic
def registrar_pago_de_cuenta(
    *,
    cuenta_id: int,
    negocio_id: int,
    monto: Decimal,
    metodo: str,
    recibido_por_id: int,
    referencia_transaccion: str = "",
) -> ResultadoDeCobroDTO:
    """Cobra la cuenta de una persona y la libera.

    **Bloquea la cuenta antes de cobrar.** Dos cajeros cobrando la misma
    pulsera a la vez generarían dos `PagoEvento` y la caja del día cuadraría de
    más, y la restricción `pulsera_con_una_sola_asignacion_activa` **no lo
    impide**: impide dos asignaciones activas, no dos cierres. Por eso se
    bloquea y se vuelve a comprobar `liberada_en` **después** del bloqueo.

    Raises:
        NoEncontradoEnEsteNegocio, CuentaYaLiberada, PagoNoCubreElConsumo.
    """
    cuenta = repositorio_de_cuentas.bloquear(cuenta_id=cuenta_id, negocio_id=negocio_id)
    if cuenta is None:
        raise NoEncontradoEnEsteNegocio
    if cuenta.liberada_en is not None:
        raise CuentaYaLiberada

    consumido = saldos.consumo_de_una_cuenta(cliente_evento_id=cuenta.id, negocio_id=negocio_id)
    _exigir_que_cubra(monto=monto, consumido=consumido)

    pago = repositorio.crear_pago(
        negocio_id=negocio_id,
        evento_id=cuenta.grupo_evento.evento_id,
        grupo_evento_id=cuenta.grupo_evento_id,
        cliente_evento_id=cuenta.id,
        pedido_evento_id=None,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )

    cuenta.liberada_en = timezone.now()
    cuenta.liberada_por_id = recibido_por_id
    cuenta.save(update_fields=["liberada_en", "liberada_por", "actualizado_en"])

    return ResultadoDeCobroDTO(
        pago_id=pago.id, consumido=consumido, monto=monto, cuentas_liberadas=1
    )


@transaction.atomic
def registrar_pago_de_grupo(
    *,
    grupo_id: int,
    negocio_id: int,
    monto: Decimal,
    metodo: str,
    recibido_por_id: int,
    referencia_transaccion: str = "",
) -> ResultadoDeCobroDTO:
    """Cobra la mesa entera y cierra el grupo con todas sus cuentas.

    Es el caso de las quince personas que llegan juntas y pagan de una.

    Raises:
        NoEncontradoEnEsteNegocio, GrupoCerrado, PagoNoCubreElConsumo.
    """
    grupo = obtener_grupo(grupo_id=grupo_id, negocio_id=negocio_id)
    if not grupo.esta_abierto:
        raise GrupoCerrado

    consumido = saldos.consumo_de_un_grupo(grupo_id=grupo.id, negocio_id=negocio_id)
    _exigir_que_cubra(monto=monto, consumido=consumido)

    pago = repositorio.crear_pago(
        negocio_id=negocio_id,
        evento_id=grupo.evento_id,
        grupo_evento_id=grupo.id,
        # Sin cuenta: el CHECK `pago_evento_tiene_un_solo_destino` obliga a que
        # el pago sea de una sola cosa, y este es del grupo completo.
        cliente_evento_id=None,
        pedido_evento_id=None,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )

    ahora = timezone.now()
    liberadas = repositorio_de_cuentas.abiertas_de_un_grupo(
        grupo_id=grupo.id, negocio_id=negocio_id
    ).update(liberada_en=ahora, liberada_por_id=recibido_por_id, actualizado_en=ahora)

    grupo.estado = GrupoEvento.Estado.CERRADO
    grupo.cerrado_por_id = recibido_por_id
    grupo.cerrado_en = ahora
    grupo.save(update_fields=["estado", "cerrado_por", "cerrado_en", "actualizado_en"])

    return ResultadoDeCobroDTO(
        pago_id=pago.id, consumido=consumido, monto=monto, cuentas_liberadas=liberadas
    )


@transaction.atomic
def registrar_pago_de_mostrador(
    *,
    pedido_id: int,
    negocio_id: int,
    monto: Decimal,
    metodo: str,
    recibido_por_id: int,
    referencia_transaccion: str = "",
) -> ResultadoDeCobroDTO:
    """Cobra una venta de mostrador: la de quien pide, paga y se va.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoCancelable: ya se cobró o está
            cancelada. PagoNoCubreElConsumo.
    """
    pedido = obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido.cliente_evento_id is not None:
        raise PedidoNoCancelable(
            "Esa comanda es de una cuenta abierta: se cobra al cerrar la cuenta."
        )
    if pedido.estado == PedidoEvento.Estado.CANCELADO:
        raise PedidoNoCancelable("Esa comanda está cancelada.")
    if repositorio_de_pedidos.tiene_pago(pedido_id=pedido.id, negocio_id=negocio_id):
        raise PedidoNoCancelable("Esa comanda ya se cobró.")

    consumido = saldos.consumo_de_un_pedido(pedido_id=pedido.id, negocio_id=negocio_id)
    _exigir_que_cubra(monto=monto, consumido=consumido)

    pago = repositorio.crear_pago(
        negocio_id=negocio_id,
        evento_id=pedido.evento_id,
        grupo_evento_id=None,
        cliente_evento_id=None,
        pedido_evento_id=pedido.id,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )
    return ResultadoDeCobroDTO(
        pago_id=pago.id, consumido=consumido, monto=monto, cuentas_liberadas=0
    )


def _exigir_que_cubra(*, monto: Decimal, consumido: Decimal) -> None:
    """Raises: PagoNoCubreElConsumo. Un pago de más sí se acepta: es la propina."""
    if monto < consumido:
        raise PagoNoCubreElConsumo(consumido=str(consumido), recibido=str(monto))

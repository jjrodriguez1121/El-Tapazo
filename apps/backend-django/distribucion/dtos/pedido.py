"""Datos que viajan entre la API y los servicios del canal mayorista."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineaDePedidoDTO:
    """Un producto del pedido. El precio **no** viaja aquí.

    Lo congela el servicio leyendo `producto.precio_mayorista` en el momento de
    la venta: si lo mandara quien pide, cualquiera podría fijar el precio de su
    propia mercancía.
    """

    producto_id: int
    cantidad: Decimal


@dataclass(frozen=True)
class SaldoDelPedidoDTO:
    """Cuánto vale un pedido, cuánto han abonado y cuánto falta."""

    pedido_id: int
    total: Decimal
    pagado: Decimal
    saldo: Decimal


@dataclass(frozen=True)
class ResultadoDeAbonoDTO:
    """Lo que hay que enseñar después de registrar un abono.

    Lleva el saldo que queda porque es la pregunta que sigue siempre: la tienda
    acaba de pagar y quiere saber cuánto le falta.
    """

    pago_id: int
    total: Decimal
    pagado: Decimal
    saldo: Decimal

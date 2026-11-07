"""Datos que viajan entre la API y los servicios del evento."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineaDePedidoDTO:
    """Un producto de la comanda. El precio **no** viaja aquí.

    Lo congela el servicio leyendo `producto.precio_evento` en el momento de la
    venta: si lo mandara quien pide, cualquiera podría fijar el precio de su
    propia cerveza.
    """

    producto_id: int
    cantidad: Decimal


@dataclass(frozen=True)
class ResultadoDeCobroDTO:
    """Lo que hay que enseñar después de cobrar."""

    pago_id: int
    consumido: Decimal
    monto: Decimal
    cuentas_liberadas: int

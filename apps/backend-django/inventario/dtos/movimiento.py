"""Datos que viajan entre la API y los servicios del inventario."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineaDeMovimientoDTO:
    """Una línea de kardex: qué producto, en qué sitio y cuánto **con signo**.

    Positiva suma al inventario, negativa resta. El tipo del movimiento y su
    referencia no van aquí sino en la llamada, porque todas las líneas de una
    misma operación los comparten: las dos filas de un traslado son el mismo
    traslado.
    """

    producto_id: int
    ubicacion_id: int
    cantidad: Decimal


@dataclass(frozen=True)
class LineaDeProductoDTO:
    """Un producto y cuánto, **siempre en positivo**.

    Es lo que reciben los servicios de arriba —una entrada de mercancía, una
    venta, una merma—: quien los llama dice "tres cervezas", y el signo lo pone
    el servicio según lo que esté haciendo. Pedirle el signo a quien llama es
    pedirle que se equivoque."""

    producto_id: int
    cantidad: Decimal

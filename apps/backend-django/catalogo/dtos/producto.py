"""Datos que viajan entre la API y los servicios del catálogo."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DatosDeProductoDTO:
    """Lo que hace falta para crear o actualizar un producto.

    Va como DTO y no como seis argumentos sueltos porque son seis datos
    relacionados que siempre viajan juntos.
    """

    sku: str
    nombre: str
    categoria_id: int
    costo: Decimal
    precio_evento: Decimal
    precio_mayorista: Decimal


@dataclass(frozen=True)
class MargenDeVentaDTO:
    """El margen de un producto en los dos canales.

    Los márgenes son `None` cuando el costo es cero: sin costo no hay margen
    que calcular, y devolver 0 % o infinito sería inventarse un número.
    """

    costo: Decimal
    precio_evento: Decimal
    precio_mayorista: Decimal
    margen_evento: Decimal | None
    margen_mayorista: Decimal | None

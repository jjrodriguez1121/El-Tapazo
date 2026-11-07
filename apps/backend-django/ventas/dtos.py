from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class LineaDeVentaDTO:
    producto_id: int
    cantidad: Decimal


@dataclass(frozen=True)
class DatosDeVentaDTO:
    ubicacion_id: int
    lineas: list[LineaDeVentaDTO]
    tipo_pago: str
    cliente_id: int | None = None
    fecha_vencimiento: date | None = None
    metodo_pago: str | None = None
    referencia_transaccion: str = ""
    observaciones: str = ""

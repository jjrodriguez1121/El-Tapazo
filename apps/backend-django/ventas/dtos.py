from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class LineaDeVentaDTO:
    producto_id: int
    cantidad: Decimal


@dataclass(frozen=True)
class DatosDeVentaDTO:
    lineas: list[LineaDeVentaDTO]
    tipo_pago: str
    descuento_porcentaje: Decimal = Decimal("0")
    cliente_id: int | None = None
    fecha_vencimiento: date | None = None
    metodo_pago_id: int | None = None
    referencia_transaccion: str = ""
    observaciones: str = ""
    estado_entrega: str = "pendiente_entrega"

"""Datos que viajan entre la API y los servicios de clientes."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DatosDeClienteDTO:
    """La ficha de una persona que compra en el bar.

    Va como DTO porque son siete datos que siempre viajan juntos. El documento
    (tipo y número) es lo que identifica a la persona: por eso no se separa.
    """

    tipo_documento: str
    numero_documento: str
    nombre: str
    apellido: str
    fecha_nacimiento: date
    telefono: str = ""
    correo: str = ""
    notas: str = ""

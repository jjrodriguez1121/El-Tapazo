"""Datos que viajan entre la API y los servicios de las tiendas cliente."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DatosDeClienteDistribucionDTO:
    """La ficha de una tienda a la que se le vende al por mayor.

    Va como DTO porque son ocho datos que siempre viajan juntos. El NIT es lo
    que identifica a la tienda —igual que el documento identifica a la persona
    del bar—, y `dias_credito` en 0 significa que paga de contado, no que no
    tiene plazo definido.
    """

    razon_social: str
    nit: str
    nombre_contacto: str = ""
    telefono: str = ""
    correo: str = ""
    ciudad: str = ""
    direccion: str = ""
    dias_credito: int = 0

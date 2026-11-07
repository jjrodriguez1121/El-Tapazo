"""Formato del SKU.

Se valida en un solo sitio y se usa desde el servicio: el serializer comprueba
la **forma** de la petición (que venga, que sea texto), y esto comprueba la
**regla del negocio** (que el código tenga la pinta acordada).
"""

import re

from catalogo.excepciones import FormatoSkuInvalido

# Tres letras, un guion y de tres a seis cifras: CER-001, LIC-1234.
PATRON_SKU = re.compile(r"^[A-Z]{3}-\d{3,6}$")


def normalizar_sku(sku: str) -> str:
    """Quita espacios y sube a mayúsculas. `cer-001` y ` CER-001 ` son el mismo."""
    return sku.strip().upper()


def validar_formato_sku(sku: str) -> None:
    """Comprueba que el SKU ya normalizado cumple el patrón.

    Raises:
        FormatoSkuInvalido: no tiene la forma acordada.
    """
    if not PATRON_SKU.match(sku):
        raise FormatoSkuInvalido(sku=sku)

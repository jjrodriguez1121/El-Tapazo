"""Errores propios del dominio del catálogo."""

from catalogo.excepciones.catalogo import (
    CategoriaDuplicada,
    FormatoSkuInvalido,
    NitDeProveedorDuplicado,
    ProveedorYaAsociado,
    SkuDuplicado,
)

__all__ = [
    "CategoriaDuplicada",
    "FormatoSkuInvalido",
    "NitDeProveedorDuplicado",
    "ProveedorYaAsociado",
    "SkuDuplicado",
]

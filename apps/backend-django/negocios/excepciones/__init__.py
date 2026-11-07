"""Errores propios del dominio de negocios."""

from negocios.excepciones.negocios import (
    NegocioNoEncontrado,
    NegocioYaActivo,
    NegocioYaSuspendido,
    NitDeNegocioDuplicado,
    RangoDeFechasInvalido,
)

__all__ = [
    "NegocioNoEncontrado",
    "NegocioYaActivo",
    "NegocioYaSuspendido",
    "NitDeNegocioDuplicado",
    "RangoDeFechasInvalido",
]

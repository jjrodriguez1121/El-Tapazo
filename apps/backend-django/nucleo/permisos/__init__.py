"""Permisos de DRF compartidos por todas las apps."""

from nucleo.permisos.roles import EsAdministrador, EsCajeroOAdministrador, EsDelEquipo

__all__ = ["EsAdministrador", "EsCajeroOAdministrador", "EsDelEquipo"]

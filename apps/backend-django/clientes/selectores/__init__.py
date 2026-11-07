"""Consultas de negocio de clientes (solo lectura)."""

from clientes.selectores.clientes import (
    buscar_por_documento,
    clientes_del_negocio,
    obtener_cliente,
)

__all__ = [
    "buscar_por_documento",
    "clientes_del_negocio",
    "obtener_cliente",
]

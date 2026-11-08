"""Consultas de negocio de clientes (solo lectura)."""

from clientes.selectores.clientes import (
    buscar_por_documento,
    clientes_del_negocio,
    obtener_cliente,
)
from clientes.selectores.consumo import historial_de_consumo

__all__ = [
    "buscar_por_documento",
    "clientes_del_negocio",
    "historial_de_consumo",
    "obtener_cliente",
]

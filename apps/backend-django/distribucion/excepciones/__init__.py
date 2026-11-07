"""Errores propios del dominio mayorista."""

from distribucion.excepciones.distribucion import (
    MotivoObligatorio,
    NitDuplicado,
    PagoSuperaElTotal,
    PedidoNoCancelable,
    PedidoNoCobrable,
    PedidoNoDespachable,
    PedidoNoEntregable,
    PedidoSinLineas,
)

__all__ = [
    "MotivoObligatorio",
    "NitDuplicado",
    "PagoSuperaElTotal",
    "PedidoNoCancelable",
    "PedidoNoCobrable",
    "PedidoNoDespachable",
    "PedidoNoEntregable",
    "PedidoSinLineas",
]

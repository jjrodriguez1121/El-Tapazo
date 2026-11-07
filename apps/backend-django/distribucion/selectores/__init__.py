"""Consultas de negocio del canal mayorista (solo lectura)."""

from distribucion.selectores.clientes import (
    clientes_del_negocio,
    clientes_en_mora,
    obtener_cliente,
)
from distribucion.selectores.informes import ventas_del_canal
from distribucion.selectores.pedidos import (
    detalles_de_un_pedido,
    obtener_pedido,
    pagos_de_un_pedido,
    pedidos_del_cliente,
    pedidos_del_negocio,
)
from distribucion.selectores.saldos import (
    saldo_de_un_cliente,
    saldo_de_un_pedido,
    total_de_un_pedido,
)

__all__ = [
    "clientes_del_negocio",
    "clientes_en_mora",
    "detalles_de_un_pedido",
    "obtener_cliente",
    "obtener_pedido",
    "pagos_de_un_pedido",
    "pedidos_del_cliente",
    "pedidos_del_negocio",
    "saldo_de_un_cliente",
    "saldo_de_un_pedido",
    "total_de_un_pedido",
    "ventas_del_canal",
]

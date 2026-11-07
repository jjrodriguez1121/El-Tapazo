"""Cuánto vale un pedido, cuánto han abonado y cuánto falta.

**Lo suma la base de datos, no Python.** Traerse las líneas para sumarlas es el
antipatrón explícito de las reglas, y aquí la lista crece con cada pedido del
mes.

Los importes se cuantizan a dos decimales al final: el producto de dos
`DecimalField(12, 2)` sale con cuatro, y el número que ve la tienda son pesos.
"""

from decimal import Decimal

from distribucion.dtos import SaldoDelPedidoDTO
from distribucion.repositorios import pagos as repositorio_de_pagos
from distribucion.repositorios import pedidos as repositorio
from distribucion.selectores.clientes import obtener_cliente
from distribucion.selectores.pedidos import obtener_pedido

CENTAVOS = Decimal("0.01")


def total_de_un_pedido(*, pedido_id: int, negocio_id: int) -> Decimal:
    """Lo que vale el pedido a precio congelado.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    return repositorio.total_de(pedido_id=pedido_id, negocio_id=negocio_id).quantize(CENTAVOS)


def saldo_de_un_pedido(*, pedido_id: int, negocio_id: int) -> SaldoDelPedidoDTO:
    """Lo que vale, lo que lleva abonado y lo que falta.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    total = repositorio.total_de(pedido_id=pedido_id, negocio_id=negocio_id).quantize(CENTAVOS)
    pagado = repositorio_de_pagos.pagado_de_un_pedido(
        pedido_id=pedido_id, negocio_id=negocio_id
    ).quantize(CENTAVOS)
    return SaldoDelPedidoDTO(pedido_id=pedido_id, total=total, pagado=pagado, saldo=total - pagado)


def saldo_de_un_cliente(*, cliente_id: int, negocio_id: int) -> Decimal:
    """Lo que una tienda debe **en total**, esté vencido o no.

    Los pedidos cancelados no cuentan: la mercancía nunca salió de la bodega,
    así que no hay nada que cobrar.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    facturado = repositorio.facturado_de_un_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    pagado = repositorio_de_pagos.pagado_de_un_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    return (facturado - pagado).quantize(CENTAVOS)

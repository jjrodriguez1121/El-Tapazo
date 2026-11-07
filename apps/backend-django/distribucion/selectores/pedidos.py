"""Lecturas de los pedidos mayoristas."""

from django.db.models import QuerySet

from distribucion.models import (
    DetallePedidoDistribucion,
    PagoDistribucion,
    PedidoDistribucion,
)
from distribucion.repositorios import pagos as repositorio_de_pagos
from distribucion.repositorios import pedidos as repositorio
from distribucion.selectores.clientes import obtener_cliente
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def pedidos_del_negocio(*, negocio_id: int) -> QuerySet[PedidoDistribucion]:
    """Todos los pedidos mayoristas, del más reciente al más viejo."""
    return repositorio.del_negocio(negocio_id=negocio_id).select_related(
        "cliente_distribucion", "usuario"
    )


def obtener_pedido(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion:
    """Raises: NoEncontradoEnEsteNegocio: no existe, o es de otro negocio."""
    pedido = repositorio.obtener_del_negocio(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido is None:
        raise NoEncontradoEnEsteNegocio
    return pedido


def pedidos_del_cliente(*, cliente_id: int, negocio_id: int) -> QuerySet[PedidoDistribucion]:
    """Lo que esa tienda ha pedido, con sus líneas ya cargadas.

    Sin el `prefetch_related`, un historial de cien pedidos son cien consultas
    de más — y contra Supabase eso son cien viajes por internet.

    Raises:
        NoEncontradoEnEsteNegocio: esa tienda no es de este negocio.
    """
    obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    return (
        repositorio.de_un_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
        .select_related("cliente_distribucion", "usuario")
        .prefetch_related("detalles__producto")
    )


def detalles_de_un_pedido(
    *, pedido_id: int, negocio_id: int
) -> QuerySet[DetallePedidoDistribucion]:
    """Las líneas de un pedido, con su producto.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    return repositorio.detalles_de(pedido_id=pedido_id, negocio_id=negocio_id)


def pagos_de_un_pedido(*, pedido_id: int, negocio_id: int) -> QuerySet[PagoDistribucion]:
    """Los abonos que la tienda ha hecho contra ese pedido.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    return repositorio_de_pagos.de_un_pedido(pedido_id=pedido_id, negocio_id=negocio_id)

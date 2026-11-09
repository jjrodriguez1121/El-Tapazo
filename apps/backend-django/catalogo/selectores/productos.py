"""Lecturas del catálogo.

Un selector no escribe nunca. Compone sobre los repositorios: añade el
`select_related` que evita el N+1 y traduce el "no está" a la excepción del
dominio, que es lo que el repositorio no hace.
"""

from decimal import Decimal

from django.db.models import Count, Q, QuerySet

from catalogo.dtos import MargenDeVentaDTO
from catalogo.models import Categoria, Producto, Proveedor
from catalogo.repositorios import categorias as repositorio_de_categorias
from catalogo.repositorios import productos as repositorio
from catalogo.repositorios import proveedores as repositorio_de_proveedores
from catalogo.validadores import normalizar_sku
from nucleo.excepciones import NoEncontradoEnEsteNegocio

# Dos decimales, los mismos con los que se guarda el dinero.
CENTAVOS = Decimal("0.01")


def productos_del_negocio(*, negocio_id: int) -> QuerySet[Producto]:
    """El catálogo de un negocio, con su categoría ya cargada.

    Sin el `select_related`, un listado de veinte productos son veinte
    consultas de más — y contra Supabase eso son veinte viajes por internet.
    """
    return repositorio.del_negocio(negocio_id=negocio_id).select_related("categoria")


def obtener_producto(*, producto_id: int, negocio_id: int) -> Producto:
    """Raises: NoEncontradoEnEsteNegocio: no existe, o es de otro negocio."""
    producto = repositorio.obtener_del_negocio(producto_id=producto_id, negocio_id=negocio_id)
    if producto is None:
        raise NoEncontradoEnEsteNegocio
    return producto


def buscar_por_sku(*, negocio_id: int, sku: str) -> Producto:
    """El producto con ese SKU. Normaliza antes de buscar: `cer-001` también vale.

    Raises:
        NoEncontradoEnEsteNegocio: ningún producto del negocio tiene ese SKU.
    """
    producto = repositorio.obtener_por_sku(negocio_id=negocio_id, sku=normalizar_sku(sku))
    if producto is None:
        raise NoEncontradoEnEsteNegocio
    return producto


def obtener_categoria(*, categoria_id: int, negocio_id: int) -> Categoria:
    """Raises: NoEncontradoEnEsteNegocio."""
    categoria = repositorio_de_categorias.obtener_del_negocio(
        categoria_id=categoria_id, negocio_id=negocio_id
    )
    if categoria is None:
        raise NoEncontradoEnEsteNegocio
    return categoria


def categorias_del_negocio(*, negocio_id: int) -> QuerySet[Categoria]:
    return repositorio_de_categorias.del_negocio(negocio_id=negocio_id)


def obtener_proveedor(*, proveedor_id: int, negocio_id: int) -> Proveedor:
    """Raises: NoEncontradoEnEsteNegocio."""
    proveedor = repositorio_de_proveedores.obtener_del_negocio(
        proveedor_id=proveedor_id, negocio_id=negocio_id
    )
    if proveedor is None:
        raise NoEncontradoEnEsteNegocio
    return proveedor


def proveedores_del_negocio(*, negocio_id: int) -> QuerySet[Proveedor]:
    return repositorio_de_proveedores.del_negocio(negocio_id=negocio_id).annotate(
        cantidad_productos=Count(
            "compras__detalles__producto",
            filter=Q(compras__estado="RECIBIDA"),
            distinct=True,
        )
    )


def margen_de_venta(*, producto_id: int, negocio_id: int) -> MargenDeVentaDTO:
    """Cuánto se le gana al producto, en porcentaje sobre el costo.

    Con el costo en cero devuelve `None` en vez de un número: sin costo no hay
    margen que calcular, y contestar 0 % o infinito sería inventárselo.
    """
    producto = obtener_producto(producto_id=producto_id, negocio_id=negocio_id)
    return MargenDeVentaDTO(
        costo=producto.costo,
        precio_venta=producto.precio_venta,
        margen=_porcentaje_sobre(producto.costo, producto.precio_venta),
    )


def _porcentaje_sobre(costo: Decimal, precio: Decimal) -> Decimal | None:
    if costo <= 0:
        return None
    return ((precio - costo) / costo * 100).quantize(CENTAVOS)

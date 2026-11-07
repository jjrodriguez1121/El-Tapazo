"""Consultas al ORM sobre `productos_proveedores`: a cuánto vende cada proveedor.

Tiene módulo propio, y no vive dentro de `productos.py` ni de `proveedores.py`,
porque su servicio (`servicios/ofertas.py`) es el que necesita estas consultas
y sin él tendría que escribir `ProductoProveedor.objects` a mano.
"""

from decimal import Decimal

from django.db.models import QuerySet
from django.utils import timezone

from catalogo.models import ProductoProveedor


def obtener(*, producto_id: int, proveedor_id: int, negocio_id: int) -> ProductoProveedor | None:
    return ProductoProveedor.objects.filter(
        producto_id=producto_id, proveedor_id=proveedor_id, negocio_id=negocio_id
    ).first()


def de_un_producto(*, producto_id: int, negocio_id: int) -> QuerySet[ProductoProveedor]:
    return ProductoProveedor.objects.filter(producto_id=producto_id, negocio_id=negocio_id)


def existe(*, producto_id: int, proveedor_id: int) -> bool:
    return ProductoProveedor.objects.filter(
        producto_id=producto_id, proveedor_id=proveedor_id
    ).exists()


def crear(
    *,
    negocio_id: int,
    producto_id: int,
    proveedor_id: int,
    precio_compra: Decimal,
    codigo_proveedor: str,
    es_principal: bool,
) -> ProductoProveedor:
    return ProductoProveedor.objects.create(
        negocio_id=negocio_id,
        producto_id=producto_id,
        proveedor_id=proveedor_id,
        precio_compra=precio_compra,
        codigo_proveedor=codigo_proveedor,
        es_principal=es_principal,
    )


def quitar_principal(*, producto_id: int) -> int:
    """Deja sin proveedor habitual a ese producto. Devuelve cuántas filas cambió.

    Va con `update()` sobre el queryset y no fila a fila: la restricción parcial
    `producto_con_un_solo_proveedor_principal` obliga a que el anterior deje de
    serlo **antes** de que el nuevo lo sea, dentro de la misma transacción.

    `actualizado_en` va explícito porque un `update()` **no dispara `auto_now`**:
    sin esta línea la columna se quedaría congelada en la fecha de creación.
    """
    return ProductoProveedor.objects.filter(producto_id=producto_id, es_principal=True).update(
        es_principal=False, actualizado_en=timezone.now()
    )

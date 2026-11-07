"""Consultas al ORM sobre `productos`."""

from decimal import Decimal

from django.db.models import QuerySet

from catalogo.models import Producto


def obtener_del_negocio(*, producto_id: int, negocio_id: int) -> Producto | None:
    return (
        Producto.objects.select_related("categoria")
        .filter(pk=producto_id, negocio_id=negocio_id)
        .first()
    )


def obtener_por_sku(*, negocio_id: int, sku: str) -> Producto | None:
    return (
        Producto.objects.select_related("categoria").filter(negocio_id=negocio_id, sku=sku).first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[Producto]:
    return Producto.objects.filter(negocio_id=negocio_id)


def todos_son_del_negocio(*, producto_ids: set[int], negocio_id: int) -> bool:
    """Una sola consulta para varios ids: comprobarlos de uno en uno sería N+1."""
    return Producto.objects.filter(pk__in=producto_ids, negocio_id=negocio_id).count() == len(
        producto_ids
    )


def existe_sku(*, negocio_id: int, sku: str, excluyendo_id: int | None = None) -> bool:
    consulta = Producto.objects.filter(negocio_id=negocio_id, sku=sku)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(
    *,
    negocio_id: int,
    sku: str,
    nombre: str,
    categoria_id: int,
    costo: Decimal,
    precio_evento: Decimal,
    precio_mayorista: Decimal,
) -> Producto:
    return Producto.objects.create(
        negocio_id=negocio_id,
        sku=sku,
        nombre=nombre,
        categoria_id=categoria_id,
        costo=costo,
        precio_evento=precio_evento,
        precio_mayorista=precio_mayorista,
    )

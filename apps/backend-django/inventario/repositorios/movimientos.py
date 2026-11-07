"""Consultas al ORM sobre `movimientos_inventario`, el kardex.

De aquí **no se borra nunca**: un movimiento equivocado se corrige con un
movimiento contrario, y los dos quedan. Por eso este módulo no tiene `borrar`.
"""

from decimal import Decimal

from django.db.models import QuerySet, Sum
from django.utils import timezone

from inventario.models import MovimientoInventario


def crear_en_lote(*, movimientos: list[MovimientoInventario]) -> list[MovimientoInventario]:
    """Inserta las filas del kardex de una vez.

    `bulk_create` **no ejecuta las validaciones de Python**, así que las
    cantidades ya vienen comprobadas por el servicio: una línea en cero saldría
    como `IntegrityError` y llegaría al cliente como un 500.
    """
    return MovimientoInventario.objects.bulk_create(movimientos)


def obtener_del_negocio(*, movimiento_id: int, negocio_id: int) -> MovimientoInventario | None:
    return (
        MovimientoInventario.objects.select_related("producto", "ubicacion")
        .filter(pk=movimiento_id, negocio_id=negocio_id)
        .first()
    )


def de_un_producto(*, producto_id: int, negocio_id: int) -> QuerySet[MovimientoInventario]:
    """Usa `movimiento_producto_fecha_idx`: es la consulta estrella del kardex."""
    return MovimientoInventario.objects.filter(producto_id=producto_id, negocio_id=negocio_id)


def de_una_referencia(
    *, referencia_tipo: str, referencia_id: int, negocio_id: int
) -> QuerySet[MovimientoInventario]:
    """Usa `movimiento_referencia_idx`: de un pedido a lo que movió."""
    return MovimientoInventario.objects.filter(
        referencia_tipo=referencia_tipo, referencia_id=referencia_id, negocio_id=negocio_id
    )


def neto_por_referencia(*, referencia_tipo: str, referencia_id: int, negocio_id: int) -> list[dict]:
    """Cuánto movió esa referencia **en neto**, por producto y ubicación.

    Es el neto y no las líneas del pedido a propósito: un pedido que se
    despachó, no se pudo entregar y se volvió a despachar acumula −X, +X, −X en
    el kardex, y solo el neto sabe cuánto está fuera de verdad. Sumar las
    líneas del pedido devolvería el doble.
    """
    return list(
        de_una_referencia(
            referencia_tipo=referencia_tipo, referencia_id=referencia_id, negocio_id=negocio_id
        )
        .values("producto_id", "ubicacion_id")
        .annotate(neto=Sum("cantidad"))
        .order_by("producto_id", "ubicacion_id")
    )


def saldo_segun_kardex(*, producto_id: int, ubicacion_id: int, negocio_id: int) -> Decimal:
    """`SUM(cantidad)` es el saldo, sin mirar el tipo: la cantidad lleva signo."""
    total = MovimientoInventario.objects.filter(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    ).aggregate(total=Sum("cantidad"))["total"]
    return total if total is not None else Decimal("0.00")


def esta_anulado(*, movimiento_id: int, negocio_id: int) -> bool:
    """Si ya existe su contrario.

    La anulación se escribe con `referencia_tipo="ajuste"` y el id del
    movimiento anulado, así que se detecta sin tocar el esquema. No choca con
    un ajuste manual, que lleva la referencia vacía.
    """
    return MovimientoInventario.objects.filter(
        referencia_tipo=MovimientoInventario.ReferenciaTipo.AJUSTE,
        referencia_id=movimiento_id,
        negocio_id=negocio_id,
    ).exists()


def fijar_referencia(*, movimiento_ids: list[int], referencia_id: int) -> None:
    """Ata varias filas a la misma referencia, ya conocido su id.

    Lo necesita el traslado: sus dos filas comparten `referencia_id`, y ese id
    no existe hasta que la primera está insertada.
    """
    MovimientoInventario.objects.filter(pk__in=movimiento_ids).update(
        referencia_id=referencia_id, actualizado_en=timezone.now()
    )

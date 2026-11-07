"""Consultas al ORM sobre `pedidos_evento` y su detalle."""

from datetime import date
from decimal import Decimal

from django.db.models import F, QuerySet, Sum

from eventos.models import DetallePedidoEvento, PagoEvento, PedidoEvento


def obtener_del_negocio(*, pedido_id: int, negocio_id: int) -> PedidoEvento | None:
    return (
        PedidoEvento.objects.select_related("cliente_evento", "evento")
        .filter(pk=pedido_id, negocio_id=negocio_id)
        .first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[PedidoEvento]:
    return PedidoEvento.objects.filter(negocio_id=negocio_id)


def crear(
    *,
    negocio_id: int,
    evento_id: int,
    cliente_evento_id: int | None,
    mesero_id: int,
) -> PedidoEvento:
    return PedidoEvento.objects.create(
        negocio_id=negocio_id,
        evento_id=evento_id,
        cliente_evento_id=cliente_evento_id,
        mesero_id=mesero_id,
    )


def crear_detalles(*, detalles: list[DetallePedidoEvento]) -> list[DetallePedidoEvento]:
    """`bulk_create` **no ejecuta las validaciones de Python**.

    Las cantidades y los precios ya vienen comprobados por el servicio: una
    línea en cero saldría como `IntegrityError` y llegaría al cliente como un
    500 en vez de como un error de formulario.
    """
    return DetallePedidoEvento.objects.bulk_create(detalles)


def detalles_de(*, pedido_id: int, negocio_id: int) -> QuerySet[DetallePedidoEvento]:
    return DetallePedidoEvento.objects.filter(
        pedido_evento_id=pedido_id, negocio_id=negocio_id
    ).select_related("producto")


def tiene_pago(*, pedido_id: int, negocio_id: int) -> bool:
    """Si una venta de mostrador ya se cobró. Una comanda cobrada no se cancela."""
    return PagoEvento.objects.filter(pedido_evento_id=pedido_id, negocio_id=negocio_id).exists()


def total_de(*, pedido_id: int, negocio_id: int, tipo_del_importe) -> Decimal:
    """Lo suma la base de datos, no Python."""
    total = DetallePedidoEvento.objects.filter(
        pedido_evento_id=pedido_id, negocio_id=negocio_id
    ).aggregate(total=Sum(F("cantidad") * F("precio_unitario"), output_field=tipo_del_importe))[
        "total"
    ]
    return total if total is not None else Decimal("0")


def vendido_entre(*, negocio_id: int, desde: date, hasta: date, tipo_del_importe) -> Decimal:
    """Lo que se vendió en la barra entre dos fechas, las dos incluidas.

    Las comandas canceladas no cuentan: devolvieron el producto al inventario,
    así que tampoco se cobraron.

    Se filtra por `creado_en` de la comanda y no por la fecha del evento: una
    jornada que arranca el sábado y cierra el domingo vendió en los dos días, y
    el resumen del mes tiene que poder partirla.
    """
    total = (
        DetallePedidoEvento.objects.filter(
            negocio_id=negocio_id,
            pedido_evento__creado_en__date__gte=desde,
            pedido_evento__creado_en__date__lte=hasta,
        )
        .exclude(pedido_evento__estado=PedidoEvento.Estado.CANCELADO)
        .aggregate(total=Sum(F("cantidad") * F("precio_unitario"), output_field=tipo_del_importe))[
            "total"
        ]
    )
    return total if total is not None else Decimal("0")

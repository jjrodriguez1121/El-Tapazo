"""Consultas al ORM sobre `pedidos_distribucion` y su detalle."""

from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, F, QuerySet, Sum

from distribucion.models import DetallePedidoDistribucion, PedidoDistribucion

# El producto de dos DecimalField(12, 2) no cabe en 12 dígitos, de ahí el 24.
# Y sin `output_field` Django lanza `FieldError` en una expresión mixta: la
# multiplicación de dos columnas no le dice de qué tipo es el resultado.
TIPO_DEL_IMPORTE = DecimalField(max_digits=24, decimal_places=4)

SIN_IMPORTE = Decimal("0")


def obtener_del_negocio(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion | None:
    return (
        PedidoDistribucion.objects.select_related("cliente_distribucion", "usuario")
        .filter(pk=pedido_id, negocio_id=negocio_id)
        .first()
    )


def bloquear(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion | None:
    """La fila del pedido, bloqueada hasta el final de la transacción.

    Es lo que serializa dos cajeros abonando contra el mismo pedido a la vez:
    "la suma de los pagos no supera el total" es un agregado y no se puede
    declarar como restricción de fila.
    """
    return (
        PedidoDistribucion.objects.select_for_update()
        .filter(pk=pedido_id, negocio_id=negocio_id)
        .first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[PedidoDistribucion]:
    return PedidoDistribucion.objects.filter(negocio_id=negocio_id)


def de_un_cliente(*, cliente_id: int, negocio_id: int) -> QuerySet[PedidoDistribucion]:
    return PedidoDistribucion.objects.filter(
        cliente_distribucion_id=cliente_id, negocio_id=negocio_id
    )


def crear(*, negocio_id: int, cliente_distribucion_id: int, usuario_id: int) -> PedidoDistribucion:
    return PedidoDistribucion.objects.create(
        negocio_id=negocio_id,
        cliente_distribucion_id=cliente_distribucion_id,
        usuario_id=usuario_id,
    )


def crear_detalles(*, detalles: list[DetallePedidoDistribucion]) -> list[DetallePedidoDistribucion]:
    """`bulk_create` **no ejecuta las validaciones de Python**.

    Las cantidades y los precios ya vienen comprobados por el servicio: una
    línea en cero saldría como `IntegrityError` y llegaría al cliente como un
    500 en vez de como un error de formulario.
    """
    return DetallePedidoDistribucion.objects.bulk_create(detalles)


def detalles_de(*, pedido_id: int, negocio_id: int) -> QuerySet[DetallePedidoDistribucion]:
    return DetallePedidoDistribucion.objects.filter(
        pedido_distribucion_id=pedido_id, negocio_id=negocio_id
    ).select_related("producto")


def total_de(*, pedido_id: int, negocio_id: int) -> Decimal:
    """Lo que vale el pedido. Lo multiplica y lo suma la base, no Python."""
    total = DetallePedidoDistribucion.objects.filter(
        pedido_distribucion_id=pedido_id, negocio_id=negocio_id
    ).aggregate(total=Sum(F("cantidad") * F("precio_unitario"), output_field=TIPO_DEL_IMPORTE))[
        "total"
    ]
    return total if total is not None else SIN_IMPORTE


def facturado_de_un_cliente(*, cliente_id: int, negocio_id: int) -> Decimal:
    """Todo lo que se le ha facturado a una tienda, menos lo cancelado.

    Un pedido cancelado no se cobra: la mercancía nunca salió de la bodega.
    """
    total = (
        DetallePedidoDistribucion.objects.filter(
            pedido_distribucion__cliente_distribucion_id=cliente_id, negocio_id=negocio_id
        )
        .exclude(pedido_distribucion__estado=PedidoDistribucion.Estado.CANCELADO)
        .aggregate(total=Sum(F("cantidad") * F("precio_unitario"), output_field=TIPO_DEL_IMPORTE))[
            "total"
        ]
    )
    return total if total is not None else SIN_IMPORTE


def vendido_entre(*, negocio_id: int, desde: date, hasta: date) -> Decimal:
    """Lo que se le facturó a las tiendas entre dos fechas, las dos incluidas.

    Se cuenta por `fecha_pedido` —cuándo se vendió— y no por la entrega: un
    pedido de fin de mes que se entrega el 2 es venta del mes en que se tomó.
    Los cancelados no cuentan: esa mercancía nunca salió de la bodega.
    """
    total = (
        DetallePedidoDistribucion.objects.filter(
            negocio_id=negocio_id,
            pedido_distribucion__fecha_pedido__date__gte=desde,
            pedido_distribucion__fecha_pedido__date__lte=hasta,
        )
        .exclude(pedido_distribucion__estado=PedidoDistribucion.Estado.CANCELADO)
        .aggregate(total=Sum(F("cantidad") * F("precio_unitario"), output_field=TIPO_DEL_IMPORTE))[
            "total"
        ]
    )
    return total if total is not None else SIN_IMPORTE

"""Consultas al ORM sobre `pagos_distribucion`."""

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet, Sum

from distribucion.models import PagoDistribucion, PedidoDistribucion
from distribucion.repositorios.pedidos import SIN_IMPORTE


def crear_pago(
    *,
    negocio_id: int,
    pedido_distribucion_id: int,
    monto: Decimal,
    metodo: str,
    referencia_transaccion: str,
    recibido_por_id: int,
) -> PagoDistribucion:
    return PagoDistribucion.objects.create(
        negocio_id=negocio_id,
        pedido_distribucion_id=pedido_distribucion_id,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion,
        recibido_por_id=recibido_por_id,
    )


def de_un_pedido(*, pedido_id: int, negocio_id: int) -> QuerySet[PagoDistribucion]:
    return PagoDistribucion.objects.filter(
        pedido_distribucion_id=pedido_id, negocio_id=negocio_id
    ).select_related("recibido_por")


def pagado_de_un_pedido(*, pedido_id: int, negocio_id: int) -> Decimal:
    """Lo que la tienda lleva abonado contra ese pedido."""
    total = PagoDistribucion.objects.filter(
        pedido_distribucion_id=pedido_id, negocio_id=negocio_id
    ).aggregate(total=Sum("monto"))["total"]
    return total if total is not None else SIN_IMPORTE


def pagado_de_un_cliente(*, cliente_id: int, negocio_id: int) -> Decimal:
    """Todo lo que ha abonado una tienda, sin contar lo de los pedidos cancelados."""
    total = (
        PagoDistribucion.objects.filter(
            pedido_distribucion__cliente_distribucion_id=cliente_id, negocio_id=negocio_id
        )
        .exclude(pedido_distribucion__estado=PedidoDistribucion.Estado.CANCELADO)
        .aggregate(total=Sum("monto"))["total"]
    )
    return total if total is not None else SIN_IMPORTE


def cobrado_entre(*, negocio_id: int, desde: date, hasta: date) -> Decimal:
    """El dinero que entró por el mayoreo entre dos fechas, las dos incluidas.

    Es lo que **abonaron** en esos días, no lo que se les facturó: una tienda a
    30 días paga el mes siguiente, y esa es justo la diferencia que el resumen
    tiene que enseñar.
    """
    total = PagoDistribucion.objects.filter(
        negocio_id=negocio_id, fecha__date__gte=desde, fecha__date__lte=hasta
    ).aggregate(total=Sum("monto"))["total"]
    return total if total is not None else SIN_IMPORTE

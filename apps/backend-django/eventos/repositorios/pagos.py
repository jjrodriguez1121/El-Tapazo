"""Consultas al ORM sobre `pagos_evento`."""

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet, Sum

from eventos.models import PagoEvento


def crear_pago(
    *,
    negocio_id: int,
    evento_id: int,
    grupo_evento_id: int | None,
    cliente_evento_id: int | None,
    pedido_evento_id: int | None,
    monto: Decimal,
    metodo: str,
    referencia_transaccion: str,
    recibido_por_id: int,
) -> PagoEvento:
    return PagoEvento.objects.create(
        negocio_id=negocio_id,
        evento_id=evento_id,
        grupo_evento_id=grupo_evento_id,
        cliente_evento_id=cliente_evento_id,
        pedido_evento_id=pedido_evento_id,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion,
        recibido_por_id=recibido_por_id,
    )


def pagos_de_un_evento(*, evento_id: int, negocio_id: int) -> QuerySet[PagoEvento]:
    return PagoEvento.objects.filter(evento_id=evento_id, negocio_id=negocio_id)


def cobrado_entre(*, negocio_id: int, desde: date, hasta: date) -> Decimal:
    """El dinero que entró por la barra entre dos fechas, las dos incluidas."""
    total = PagoEvento.objects.filter(
        negocio_id=negocio_id, fecha__date__gte=desde, fecha__date__lte=hasta
    ).aggregate(total=Sum("monto"))["total"]
    return total if total is not None else Decimal("0")

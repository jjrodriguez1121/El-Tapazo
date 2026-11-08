"""Resumen de ventas para el dashboard."""

from datetime import date

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from negocios.excepciones import RangoDeFechasInvalido
from ventas.models import PagoVenta, Venta

IMPORTE = DecimalField(max_digits=24, decimal_places=2)


def resumen_de_ventas(*, negocio_id: int, desde: date | None = None, hasta: date | None = None) -> dict:
    """Ventas registradas y pagos recibidos dentro del rango indicado."""
    desde, hasta = _rango(desde=desde, hasta=hasta)
    ventas = Venta.objects.filter(negocio_id=negocio_id, fecha__date__range=(desde, hasta)).exclude(
        estado=Venta.Estado.ANULADA
    )
    vendido = ventas.aggregate(
        total=Coalesce(
            Sum(ExpressionWrapper(F("detalles__cantidad") * F("detalles__precio_unitario"), output_field=IMPORTE)),
            0,
            output_field=IMPORTE,
        )
    )["total"]
    cobrado = PagoVenta.objects.filter(
        negocio_id=negocio_id, fecha__date__range=(desde, hasta)
    ).exclude(
        venta__estado=Venta.Estado.ANULADA
    ).aggregate(total=Coalesce(Sum("monto"), 0, output_field=IMPORTE))["total"]
    return {"desde": desde, "hasta": hasta, "vendido_total": vendido, "cobrado_total": cobrado}


def _rango(*, desde: date | None, hasta: date | None) -> tuple[date, date]:
    hoy = timezone.localdate()
    desde, hasta = desde or hoy.replace(day=1), hasta or hoy
    if desde > hasta:
        raise RangoDeFechasInvalido(desde=desde.isoformat(), hasta=hasta.isoformat())
    return desde, hasta

"""Resumen de ventas para el dashboard."""

from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from compras.models import CuentaPorPagar
from inventario.selectores import productos_bajo_minimo
from negocios.excepciones import RangoDeFechasInvalido
from ventas.models import CuentaPorCobrar, DetalleVenta, PagoVenta, Venta

IMPORTE = DecimalField(max_digits=24, decimal_places=2)
CERO = Decimal("0")


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
        negocio_id=negocio_id,
        fecha__date__range=(desde, hasta),
        estado=PagoVenta.Estado.CONFIRMADO,
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


def resumen_del_dashboard(*, negocio_id: int, desde: date, hasta: date) -> dict:
    """Indicadores financieros y operativos de un periodo cerrado.

    La utilidad corresponde a la utilidad bruta: ventas netas menos el costo
    de los productos vendidos. Los gastos operativos se registrarán después.
    """
    desde, hasta = _rango(desde=desde, hasta=hasta)
    ventas = Venta.objects.filter(
        negocio_id=negocio_id, fecha__date__range=(desde, hasta)
    ).exclude(estado=Venta.Estado.ANULADA)
    totales = ventas.aggregate(
        facturado=Coalesce(Sum("total"), CERO, output_field=IMPORTE),
        descuentos=Coalesce(Sum("descuento"), CERO, output_field=IMPORTE),
        impuestos=Coalesce(Sum("total_iva"), CERO, output_field=IMPORTE),
    )
    costo_ventas = DetalleVenta.objects.filter(venta__in=ventas).aggregate(
        total=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("cantidad") * F("costo_unitario"), output_field=IMPORTE
                )
            ),
            CERO,
            output_field=IMPORTE,
        )
    )["total"]
    productos_mas_vendidos = list(
        DetalleVenta.objects.filter(venta__in=ventas)
        .values("producto_id", "producto__nombre")
        .annotate(
            unidades=Coalesce(Sum("cantidad"), CERO, output_field=IMPORTE),
            total=Coalesce(Sum("subtotal"), CERO, output_field=IMPORTE),
        )
        .order_by("-unidades", "producto__nombre")[:5]
    )
    ventas_netas = totales["facturado"] - totales["impuestos"]
    utilidad_bruta = ventas_netas - costo_ventas
    por_cobrar = CuentaPorCobrar.objects.filter(negocio_id=negocio_id).exclude(
        estado__in=[CuentaPorCobrar.Estado.PAGADA, CuentaPorCobrar.Estado.ANULADA]
    ).aggregate(total=Coalesce(Sum("saldo"), CERO, output_field=IMPORTE))["total"]
    por_pagar = CuentaPorPagar.objects.filter(
        negocio_id=negocio_id,
        estado__in=[
            CuentaPorPagar.Estado.PENDIENTE,
            CuentaPorPagar.Estado.PARCIAL,
            CuentaPorPagar.Estado.VENCIDA,
        ],
    ).aggregate(total=Coalesce(Sum("saldo"), CERO, output_field=IMPORTE))["total"]
    cobrado = PagoVenta.objects.filter(
        negocio_id=negocio_id,
        fecha__date__range=(desde, hasta),
        estado=PagoVenta.Estado.CONFIRMADO,
    ).exclude(venta__estado=Venta.Estado.ANULADA).aggregate(
        total=Coalesce(Sum("monto"), CERO, output_field=IMPORTE)
    )["total"]

    return {
        "desde": desde,
        "hasta": hasta,
        "ventas_facturadas": totales["facturado"],
        "ventas_netas": ventas_netas,
        "descuentos": totales["descuentos"],
        "impuestos": totales["impuestos"],
        "costo_de_ventas": costo_ventas,
        "utilidad_bruta": utilidad_bruta,
        "cobrado_en_periodo": cobrado,
        "por_cobrar": por_cobrar,
        "por_pagar": por_pagar,
        "ventas_registradas": ventas.count(),
        "ventas_contado": ventas.filter(tipo_pago=Venta.TipoPago.CONTADO).count(),
        "ventas_credito": ventas.filter(tipo_pago=Venta.TipoPago.CREDITO).count(),
        "productos_mas_vendidos": [
            {
                "id": producto["producto_id"],
                "nombre": producto["producto__nombre"],
                "unidades": producto["unidades"],
                "total": producto["total"],
            }
            for producto in productos_mas_vendidos
        ],
        "entregas_pendientes": ventas.filter(
            estado_entrega=Venta.EstadoEntrega.PENDIENTE
        ).count(),
        "stock_bajo": productos_bajo_minimo(negocio_id=negocio_id).count(),
    }

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from nucleo.permisos import EsAdministrador
from ventas.models import CuentaPorCobrar


@api_view(["GET"])
@permission_classes([EsAdministrador])
def cuentas_por_cobrar(request):
    hoy = timezone.localdate()
    cuentas = (
        CuentaPorCobrar.objects.filter(
            negocio_id=request.user.negocio_id,
        )
        .exclude(estado=CuentaPorCobrar.Estado.PAGADA)
        .select_related("venta__cliente")
        .order_by("fecha_vencimiento")
    )

    datos = []
    for cuenta in cuentas:
        estado = (
            CuentaPorCobrar.Estado.VENCIDA
            if cuenta.fecha_vencimiento < hoy and cuenta.saldo > 0
            else cuenta.estado
        )
        cliente = cuenta.venta.cliente
        cliente_nombre = (
            f"{cliente.nombre} {cliente.apellido}".strip()
            if cliente
            else "Cliente sin registrar"
        )
        datos.append(
            {
                "id": cuenta.id,
                "venta_id": cuenta.venta_id,
                "numero_venta": cuenta.venta.numero_venta or f"VEN-{cuenta.venta_id:04d}",
                "cliente": cliente_nombre,
                "fecha_vencimiento": cuenta.fecha_vencimiento,
                "total": cuenta.total,
                "saldo": cuenta.saldo,
                "estado": estado.upper(),
            }
        )
    return Response(datos)

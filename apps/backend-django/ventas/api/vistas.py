from decimal import Decimal
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from nucleo.permisos import EsAdministrador, EsCajeroOAdministrador
from ventas.models import CuentaPorCobrar, MetodoPago, PagoVenta, Venta
from ventas.dtos import DatosDeVentaDTO, LineaDeVentaDTO
from ventas.servicios import registrar_abono as registrar_abono_cartera, registrar_venta


@api_view(["GET", "POST"])
@permission_classes([EsCajeroOAdministrador])
def ventas(request):
    if request.method == "GET":
        registros = (
            Venta.objects.filter(negocio_id=request.user.negocio_id)
            .select_related("cliente", "vendedor")
            .prefetch_related("detalles")
            .order_by("-fecha")
        )
        datos = []
        for v in registros:
            cliente_nombre = (
                f"{v.cliente.nombre} {v.cliente.apellido}".strip()
                if v.cliente
                else "Cliente general / Mostrador"
            )
            vendedor_nombre = (
                f"{v.vendedor.nombre} {v.vendedor.apellido}".strip()
                if v.vendedor
                else "N/D"
            )
            datos.append({
                "id": v.id,
                "numero_venta": v.numero_venta or f"VEN-{v.id:04d}",
                "cliente_nombre": cliente_nombre,
                "vendedor": vendedor_nombre,
                "fecha_venta": v.fecha,
                "tipo_pago": v.tipo_pago,
                "estado": v.estado,
                "total": v.total,
                "subtotal": v.subtotal,
                "total_iva": v.total_iva,
                "descuento": v.descuento,
                "cantidad_items": v.detalles.count(),
            })
        return Response(datos)

    lineas = request.data.get("lineas", [])
    tipo_pago = request.data.get("tipo_pago")
    if not isinstance(lineas, list) or not lineas:
        raise ValidationError("Agregue al menos un producto.")
    try:
        datos = DatosDeVentaDTO(
            lineas=[
                LineaDeVentaDTO(
                    producto_id=int(linea["producto_id"]),
                    cantidad=Decimal(str(linea["cantidad"])),
                )
                for linea in lineas
            ],
            tipo_pago=tipo_pago,
            cliente_id=request.data.get("cliente_id") or None,
            fecha_vencimiento=request.data.get("fecha_vencimiento") or None,
            metodo_pago_id=request.data.get("metodo_pago_id") or None,
            referencia_transaccion=request.data.get("referencia_transaccion", ""),
            observaciones=request.data.get("observaciones", ""),
            descuento_porcentaje=Decimal(str(request.data.get("descuento_porcentaje", 0))),
        )
        venta = registrar_venta(
            datos=datos,
            negocio_id=request.user.negocio_id,
            vendedor_id=request.user.id,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValidationError(str(error))
    return Response({
        "id": venta.id,
        "numero_venta": venta.numero_venta,
        "total": venta.total,
        "tipo_pago": venta.tipo_pago,
        "estado": venta.estado,
    }, status=201)


@api_view(["GET"])
@permission_classes([EsCajeroOAdministrador])
def metodos_pago(request):
    metodos = MetodoPago.objects.filter(
        negocio_id=request.user.negocio_id, estado=True
    ).order_by("nombre")
    return Response([
        {"id": metodo.id, "nombre": metodo.nombre}
        for metodo in metodos
    ])


@api_view(["GET"])
@permission_classes([EsCajeroOAdministrador])
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
                "fecha_venta": cuenta.venta.fecha,
                "fecha_vencimiento": cuenta.fecha_vencimiento,
                "total": cuenta.total,
                "saldo": cuenta.saldo,
                "estado": estado.upper(),
            }
        )
    return Response(datos)


@api_view(["GET"])
@permission_classes([EsCajeroOAdministrador])
def cuenta_por_cobrar_detalle(request, cuenta_id):
    cuenta = (
        CuentaPorCobrar.objects.select_related("venta__cliente")
        .filter(id=cuenta_id, negocio_id=request.user.negocio_id)
        .first()
    )
    if cuenta is None:
        return Response({"detail": "Cuenta por cobrar no encontrada."}, status=404)

    hoy = timezone.localdate()
    estado = (
        "VENCIDA"
        if cuenta.fecha_vencimiento < hoy and cuenta.saldo > 0
        else cuenta.estado
    )
    cliente = cuenta.venta.cliente
    cliente_nombre = (
        f"{cliente.nombre} {cliente.apellido}".strip()
        if cliente
        else "Cliente sin registrar"
    )
    pagos = (
        PagoVenta.objects.filter(
            cuenta_por_cobrar=cuenta,
            negocio_id=request.user.negocio_id,
        )
        .select_related("metodo_pago")
        .order_by("-fecha")
    )
    return Response({
        "id": cuenta.id,
        "venta_id": cuenta.venta_id,
        "numero_venta": cuenta.venta.numero_venta or f"VEN-{cuenta.venta_id:04d}",
        "cliente": cliente_nombre,
        "fecha_venta": cuenta.venta.fecha,
        "fecha_vencimiento": cuenta.fecha_vencimiento,
        "total": cuenta.total,
        "saldo": cuenta.saldo,
        "abonado": cuenta.total - cuenta.saldo,
        "estado": estado.upper(),
        "abonos": [{
            "id": pago.id,
            "fecha_pago": pago.fecha,
            "valor": pago.monto,
            "metodo_pago": pago.metodo_pago.nombre if pago.metodo_pago else (pago.metodo or "N/D"),
            "referencia": pago.referencia_transaccion,
        } for pago in pagos],
    })


@api_view(["GET"])
@permission_classes([EsCajeroOAdministrador])
def venta_detalle(request, venta_id):
    venta = (
        Venta.objects.filter(id=venta_id, negocio_id=request.user.negocio_id)
        .select_related("cliente", "vendedor")
        .prefetch_related("detalles__producto")
        .first()
    )
    if not venta:
        return Response({"detail": "Venta no encontrada."}, status=404)

    cliente_nombre = (
        f"{venta.cliente.nombre} {venta.cliente.apellido}".strip()
        if venta.cliente
        else "Cliente general / Mostrador"
    )

    detalles = [
        {
            "id": d.id,
            "producto": d.producto.nombre,
            "sku": d.producto.sku,
            "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario,
            "descuento": d.descuento,
            "porcentaje_iva": d.porcentaje_iva,
            "subtotal": d.subtotal,
        }
        for d in venta.detalles.all()
    ]

    return Response({
        "id": venta.id,
        "numero_venta": venta.numero_venta or f"VEN-{venta.id:04d}",
        "fecha_venta": venta.fecha,
        "tipo_pago": venta.tipo_pago,
        "estado": venta.estado,
        "cliente_nombre": cliente_nombre,
        "vendedor": f"{venta.vendedor.nombre} {venta.vendedor.apellido}".strip() if venta.vendedor else "N/D",
        "subtotal": venta.subtotal,
        "descuento": venta.descuento,
        "total_iva": venta.total_iva,
        "total": venta.total,
        "detalles": detalles,
    })


@api_view(["POST"])
@permission_classes([EsCajeroOAdministrador])
def registrar_abono(request, cuenta_id):
    try:
        cuenta = registrar_abono_cartera(
            cuenta_id=cuenta_id,
            monto=Decimal(str(request.data["monto"])),
            metodo_pago_id=int(request.data["metodo_pago_id"]),
            recibido_por_id=request.user.id,
            negocio_id=request.user.negocio_id,
            referencia_transaccion=request.data.get("referencia", request.data.get("referencia_transaccion", "")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValidationError(str(error))
    return Response({"id": cuenta.id, "saldo": cuenta.saldo, "estado": cuenta.estado}, status=201)

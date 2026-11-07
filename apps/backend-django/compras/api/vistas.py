from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from catalogo.models import Categoria, Impuesto, Producto, Proveedor
from compras.api.serializers import CompraCrearSerializer, CompraOutputSerializer
from compras.models import Compra, CuentaPorPagar, DetalleCompra
from inventario.models import Existencia, MovimientoInventario
from nucleo.permisos import EsAdministrador


@api_view(["GET", "POST"])
@permission_classes([EsAdministrador])
def compras(request):
    negocio_id = request.user.negocio_id
    if request.method == "GET":
        registros = Compra.objects.filter(negocio_id=negocio_id).select_related(
            "proveedor"
        ).prefetch_related("detalles__producto")
        return Response(CompraOutputSerializer(registros, many=True).data)

    entrada = CompraCrearSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    return Response(_crear_compra(request=request, datos=entrada.validated_data), status=201)


@api_view(["GET"])
@permission_classes([EsAdministrador])
def compra_detalle(request, compra_id):
    compra = (
        Compra.objects.filter(id=compra_id, negocio_id=request.user.negocio_id)
        .select_related("proveedor")
        .prefetch_related("detalles__producto")
        .first()
    )
    if not compra:
        return Response({"detail": "Compra no encontrada."}, status=404)
    return Response(CompraOutputSerializer(compra).data)


@api_view(["GET"])
@permission_classes([EsAdministrador])
def cuentas_por_pagar(request):
    hoy = timezone.localdate()
    cuentas = CuentaPorPagar.objects.filter(
        negocio_id=request.user.negocio_id,
        estado__in=["PENDIENTE", "PARCIAL", "VENCIDA"],
    ).select_related("compra__proveedor").order_by("fecha_vencimiento")
    datos = []
    for cuenta in cuentas:
        estado = "VENCIDA" if cuenta.fecha_vencimiento < hoy and cuenta.saldo > 0 else cuenta.estado
        datos.append({
            "id": cuenta.id,
            "compra_id": cuenta.compra_id,
            "numero_compra": cuenta.compra.numero_compra,
            "proveedor": cuenta.compra.proveedor.razon_social,
            "fecha_vencimiento": cuenta.fecha_vencimiento,
            "total": cuenta.total,
            "saldo": cuenta.saldo,
            "estado": estado,
        })
    return Response(datos)


@transaction.atomic
def _crear_compra(*, request, datos):
    negocio_id = request.user.negocio_id
    proveedor = Proveedor.objects.filter(
        id=datos["proveedor_id"], negocio_id=negocio_id, activo=True
    ).first()
    if not proveedor:
        raise ValidationError({"proveedor_id": "Seleccione un proveedor válido."})

    compra = Compra.objects.create(
        negocio_id=negocio_id,
        proveedor=proveedor,
        usuario=request.user,
        numero_compra=_siguiente_numero_compra(negocio_id),
        numero_factura=datos.get("numero_factura", ""),
        condicion_pago=datos["condicion_pago"],
        fecha_vencimiento=datos.get("fecha_vencimiento"),
        estado=datos["estado"],
    )

    subtotal = Decimal("0")
    descuento_total = Decimal("0")
    iva_total = Decimal("0")

    for linea in datos["detalles"]:
        producto = _obtener_o_crear_producto(
            negocio_id=negocio_id, datos=linea
        )
        cantidad = linea["cantidad"]
        costo_unitario = linea["costo_unitario"]
        descuento = linea["descuento"]
        porcentaje_iva = (
            producto.impuesto.porcentaje
            if producto.impuesto_id
            else Decimal("0")
        )
        base = costo_unitario * cantidad - descuento
        valor_iva = base * porcentaje_iva / Decimal("100")

        detalle = DetalleCompra.objects.create(
            negocio_id=negocio_id,
            compra=compra,
            producto=producto,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            porcentaje_iva=porcentaje_iva,
            base_gravable=max(base, Decimal("0")),
            valor_iva=valor_iva,
            descuento=descuento,
            subtotal=base,
        )
        subtotal += base
        descuento_total += descuento
        iva_total += valor_iva

        if compra.estado == "RECIBIDA":
            _registrar_entrada_recibida(
                negocio_id=negocio_id,
                usuario=request.user,
                producto=producto,
                detalle=detalle,
                cantidad=cantidad,
                costo_unitario=costo_unitario,
            )

    compra.subtotal = subtotal
    compra.descuento = descuento_total
    compra.total_iva = iva_total
    compra.total = subtotal - descuento_total + iva_total
    compra.save(update_fields=["subtotal", "descuento", "total_iva", "total", "actualizado_en"])
    if compra.condicion_pago == "CREDITO":
        CuentaPorPagar.objects.create(
            negocio_id=negocio_id,
            compra=compra,
            fecha_vencimiento=compra.fecha_vencimiento,
            total=compra.total,
            saldo=compra.total,
        )
    return CompraOutputSerializer(compra).data


def _obtener_o_crear_producto(*, negocio_id, datos):
    if datos.get("producto_id"):
        producto = Producto.objects.filter(id=datos["producto_id"], negocio_id=negocio_id).first()
        if not producto:
            raise ValidationError({"producto_id": "Producto no encontrado en este negocio."})
        return producto

    nuevo = datos["producto_nuevo"]
    sku = nuevo["sku"].strip().upper()
    if Producto.objects.filter(negocio_id=negocio_id, sku=sku).exists():
        raise ValidationError({"producto_nuevo": "Ya existe un producto con ese SKU."})
    categoria = Categoria.objects.filter(id=nuevo["categoria_id"], negocio_id=negocio_id).first()
    if not categoria:
        raise ValidationError({"producto_nuevo": "Seleccione una categoría válida."})
    impuesto = Impuesto.objects.filter(
        id=nuevo["impuesto_id"], negocio_id=negocio_id, activo=True
    ).first()
    if not impuesto:
        raise ValidationError({"producto_nuevo": "Seleccione una tarifa de impuesto válida."})

    producto = Producto.objects.create(
        negocio_id=negocio_id,
        sku=sku,
        nombre=nuevo["nombre"].strip(),
        categoria=categoria,
        
        precio_venta=Decimal("0"),
        impuesto=impuesto,
        costo=0,
        imagen=nuevo.get("imagen", ""),
    )
    Existencia.objects.create(negocio_id=negocio_id, producto=producto, cantidad_disponible=0)
    return producto


def _registrar_entrada_recibida(*, negocio_id, usuario, producto, detalle, cantidad, costo_unitario):
    existencia, _ = Existencia.objects.select_for_update().get_or_create(
        negocio_id=negocio_id,
        producto=producto,
        defaults={"cantidad_disponible": Decimal("0")},
    )
    cantidad_anterior = Decimal(existencia.cantidad_disponible)
    costo_anterior = Decimal(existencia.costo_promedio)
    nueva_cantidad = cantidad_anterior + Decimal(cantidad)
    costo_nuevo = (
        (cantidad_anterior * costo_anterior + Decimal(cantidad) * costo_unitario) / nueva_cantidad
        if nueva_cantidad
        else costo_unitario
    )
    existencia.cantidad_disponible = nueva_cantidad
    existencia.cantidad_actual = int(nueva_cantidad)
    existencia.costo_promedio = costo_nuevo
    existencia.save(update_fields=["cantidad_disponible", "cantidad_actual", "costo_promedio", "actualizado_en"])

    producto.costo = costo_nuevo
    producto.save(update_fields=["costo", "actualizado_en"])
    if producto.precio_venta_automatico:
        margen = Decimal(producto.margen_ganancia or 0)
        producto.precio_venta = (
            costo_nuevo * (Decimal("1") + margen / Decimal("100"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        producto.save(update_fields=["precio_venta", "actualizado_en"])

    MovimientoInventario.objects.create(
        negocio_id=negocio_id,
        producto=producto,
        tipo_movimiento="ENTRADA_COMPRA",
        tipo="entrada",
        cantidad=Decimal(cantidad),
        costo_unitario=costo_unitario,
        costo_total=costo_unitario * Decimal(cantidad),
        detalle_compra=detalle,
        referencia_tipo="compra",
        referencia_id=detalle.compra_id,
        usuario=usuario,
        nota=f"Entrada por compra {detalle.compra.numero_compra}",
        fecha=timezone.now(),
    )


def _siguiente_numero_compra(negocio_id):
    ultimo = (
        Compra.objects.filter(negocio_id=negocio_id, numero_compra__startswith="COMP-")
        .order_by("-id")
        .values_list("numero_compra", flat=True)
        .first()
    )
    if not ultimo:
        return "COMP-0001"
    try:
        secuencia = int(ultimo.split("-")[-1]) + 1
    except ValueError:
        secuencia = Compra.objects.filter(negocio_id=negocio_id).count() + 1
    return f"COMP-{secuencia:04d}"

"""Operaciones atómicas para ventas y cartera."""

from decimal import Decimal

from django.db import transaction

from catalogo.models import Producto
from clientes.models import Cliente
from django.utils import timezone

from inventario.models import Existencia, MovimientoInventario
from ventas.dtos import DatosDeVentaDTO
from ventas.models import CuentaPorCobrar, DetalleVenta, MetodoPago, PagoVenta, Venta


@transaction.atomic
def registrar_venta(*, datos: DatosDeVentaDTO, negocio_id: int, vendedor_id: int) -> Venta:
    """Registra una venta, descuenta stock y cobra o crea su cartera."""
    if not datos.lineas or any(linea.cantidad <= 0 for linea in datos.lineas):
        raise ValueError("La venta debe tener líneas con cantidades positivas.")
    if datos.descuento_porcentaje < 0 or datos.descuento_porcentaje > 100:
        raise ValueError("El descuento debe estar entre 0 y 100 por ciento.")
    if datos.tipo_pago == Venta.TipoPago.CREDITO and not datos.cliente_id:
        raise ValueError("Una venta a crédito requiere cliente.")
    if datos.tipo_pago == Venta.TipoPago.CREDITO and not datos.fecha_vencimiento:
        raise ValueError("Una venta a crédito requiere fecha de vencimiento.")
    if datos.tipo_pago == Venta.TipoPago.CONTADO and not datos.metodo_pago_id:
        raise ValueError("Una venta de contado requiere medio de pago.")

    cantidades_por_producto = {}
    for linea in datos.lineas:
        cantidades_por_producto[linea.producto_id] = (
            cantidades_por_producto.get(linea.producto_id, Decimal("0")) + linea.cantidad
        )

    productos = {
        producto.id: producto
        for producto in Producto.objects.select_for_update(of=("self",)).select_related("impuesto").filter(
            negocio_id=negocio_id, activo=True, pk__in=cantidades_por_producto
        )
    }
    if len(productos) != len(cantidades_por_producto):
        raise ValueError("Uno o más productos no pertenecen al negocio o están inactivos.")
    if datos.cliente_id and not Cliente.objects.filter(pk=datos.cliente_id, negocio_id=negocio_id).exists():
        raise ValueError("El cliente no pertenece al negocio.")
    metodo_pago = None
    if datos.tipo_pago == Venta.TipoPago.CONTADO:
        metodo_pago = MetodoPago.objects.filter(
            pk=datos.metodo_pago_id, negocio_id=negocio_id, estado=True
        ).first()
        if metodo_pago is None:
            raise ValueError("El medio de pago no existe o está inactivo.")

    estado = Venta.Estado.PAGADA if datos.tipo_pago == Venta.TipoPago.CONTADO else Venta.Estado.PENDIENTE
    venta = Venta.objects.create(
        negocio_id=negocio_id,
        cliente_id=datos.cliente_id,
        vendedor_id=vendedor_id,
        tipo_pago=datos.tipo_pago,
        estado=estado,
        fecha_vencimiento=datos.fecha_vencimiento,
        numero_venta=f"VEN-{timezone.localtime().strftime('%Y%m%d')}-{Venta.objects.filter(negocio_id=negocio_id).count() + 1:04d}",
        observaciones=datos.observaciones.strip(),
    )
    detalles = []
    subtotal = Decimal("0")
    total_iva = Decimal("0")
    descuento_total = Decimal("0")
    subtotal_sin_descuento = sum(
        (cantidad * productos[producto_id].precio_venta for producto_id, cantidad in cantidades_por_producto.items()),
        Decimal("0"),
    )
    detalles_por_producto = {}
    for producto_id, cantidad in cantidades_por_producto.items():
        producto = productos[producto_id]
        precio_linea = cantidad * producto.precio_venta
        descuento_linea = (
            precio_linea * datos.descuento_porcentaje / Decimal("100")
        ).quantize(Decimal("0.01"))
        base = precio_linea - descuento_linea
        porcentaje_iva = Decimal(producto.impuesto.porcentaje) if producto.impuesto_id else Decimal("0")
        valor_iva = (base * porcentaje_iva / (Decimal("100") + porcentaje_iva)).quantize(Decimal("0.01"))
        subtotal += base - valor_iva
        total_iva += valor_iva
        descuento_total += descuento_linea
        detalles.append(DetalleVenta(
            negocio_id=negocio_id,
            venta_id=venta.id,
            producto_id=producto_id,
            cantidad=cantidad,
            costo_unitario=producto.costo,
            precio_unitario=producto.precio_venta,
            porcentaje_iva=porcentaje_iva,
            descuento=descuento_linea,
            base_gravable=base - valor_iva,
            valor_iva=valor_iva,
            subtotal=base,
        ))
    detalles_creados = DetalleVenta.objects.bulk_create(detalles)
    for detalle in detalles_creados:
        detalles_por_producto[detalle.producto_id] = detalle
    for producto_id, cantidad in cantidades_por_producto.items():
        existencia = Existencia.objects.select_for_update().filter(
            negocio_id=negocio_id, producto_id=producto_id
        ).first()
        if existencia is None or Decimal(existencia.cantidad_disponible) < cantidad:
            raise ValueError("No hay inventario suficiente para uno o más productos.")
        existencia.cantidad_disponible -= cantidad
        existencia.cantidad_actual = max(0, int(existencia.cantidad_disponible))
        existencia.save(update_fields=["cantidad_disponible", "cantidad_actual", "actualizado_en"])
        MovimientoInventario.objects.create(
            negocio_id=negocio_id,
            producto_id=producto_id,
            detalle_venta=detalles_por_producto[producto_id],
            tipo_movimiento="SALIDA_VENTA",
            tipo=MovimientoInventario.Tipo.SALIDA,
            cantidad=-cantidad,
            costo_unitario=productos[producto_id].costo,
            costo_total=productos[producto_id].costo * cantidad,
            referencia_tipo=MovimientoInventario.ReferenciaTipo.VENTA,
            referencia_id=venta.id,
            usuario_id=vendedor_id,
        )
    total = subtotal_sin_descuento - descuento_total + total_iva
    venta.subtotal = subtotal
    venta.descuento = descuento_total
    venta.total_iva = total_iva
    venta.total = total
    venta.save(update_fields=["subtotal", "descuento", "total_iva", "total", "numero_venta", "fecha_vencimiento", "actualizado_en"])
    if datos.tipo_pago == Venta.TipoPago.CONTADO:
        PagoVenta.objects.create(
            negocio_id=negocio_id,
            venta=venta,
            monto=total,
            metodo_pago=metodo_pago,
            referencia_transaccion=datos.referencia_transaccion.strip(),
            recibido_por_id=vendedor_id,
        )
    else:
        CuentaPorCobrar.objects.create(
            negocio_id=negocio_id,
            venta=venta,
            fecha_vencimiento=datos.fecha_vencimiento,
            total=total,
            saldo=total,
        )
    return venta


@transaction.atomic
def registrar_abono(*, cuenta_id: int, monto: Decimal, metodo_pago_id: int, recibido_por_id: int, negocio_id: int, referencia_transaccion: str = "") -> CuentaPorCobrar:
    """Registra un abono sin permitir que supere el saldo pendiente."""
    cuenta = CuentaPorCobrar.objects.select_for_update().select_related("venta").filter(
        pk=cuenta_id, negocio_id=negocio_id
    ).first()
    if cuenta is None:
        raise ValueError("La cuenta por cobrar no existe.")
    if monto <= 0 or monto > cuenta.saldo:
        raise ValueError("El abono debe ser mayor que cero y no superar el saldo.")
    metodo_pago = MetodoPago.objects.filter(
        pk=metodo_pago_id, negocio_id=negocio_id, estado=True
    ).first()
    if metodo_pago is None:
        raise ValueError("El medio de pago no existe o está inactivo.")
    nuevo_saldo = cuenta.saldo - monto
    PagoVenta.objects.create(
        negocio_id=negocio_id,
        venta=cuenta.venta,
        cuenta_por_cobrar=cuenta,
        monto=monto,
        metodo_pago=metodo_pago,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )
    cuenta.saldo = nuevo_saldo
    cuenta.estado = CuentaPorCobrar.Estado.PAGADA if nuevo_saldo == 0 else CuentaPorCobrar.Estado.PARCIAL
    cuenta.save(update_fields=["saldo", "estado", "actualizado_en"])
    return cuenta

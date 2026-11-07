"""Operaciones atómicas para ventas y cartera."""

from decimal import Decimal

from django.db import transaction

from catalogo.models import Producto
from clientes.models import Cliente
from inventario.dtos import LineaDeProductoDTO
from inventario.models import MovimientoInventario
from inventario.servicios import consumo
from ventas.dtos import DatosDeVentaDTO
from ventas.models import CuentaPorCobrar, DetalleVenta, PagoVenta, Venta


@transaction.atomic
def registrar_venta(*, datos: DatosDeVentaDTO, negocio_id: int, vendedor_id: int) -> Venta:
    """Registra una venta, descuenta stock y cobra o crea su cartera."""
    if not datos.lineas or any(linea.cantidad <= 0 for linea in datos.lineas):
        raise ValueError("La venta debe tener líneas con cantidades positivas.")
    if datos.tipo_pago == Venta.TipoPago.CREDITO and not datos.cliente_id:
        raise ValueError("Una venta a crédito requiere cliente.")
    if datos.tipo_pago == Venta.TipoPago.CREDITO and not datos.fecha_vencimiento:
        raise ValueError("Una venta a crédito requiere fecha de vencimiento.")
    if datos.tipo_pago == Venta.TipoPago.CONTADO and not datos.metodo_pago:
        raise ValueError("Una venta de contado requiere medio de pago.")

    productos = {
        producto.id: producto
        for producto in Producto.objects.filter(
            negocio_id=negocio_id, activo=True, pk__in={linea.producto_id for linea in datos.lineas}
        )
    }
    if len(productos) != len({linea.producto_id for linea in datos.lineas}):
        raise ValueError("Uno o más productos no pertenecen al negocio o están inactivos.")
    if datos.cliente_id and not Cliente.objects.filter(pk=datos.cliente_id, negocio_id=negocio_id).exists():
        raise ValueError("El cliente no pertenece al negocio.")

    estado = Venta.Estado.PAGADA if datos.tipo_pago == Venta.TipoPago.CONTADO else Venta.Estado.PENDIENTE
    venta = Venta.objects.create(
        negocio_id=negocio_id,
        cliente_id=datos.cliente_id,
        ubicacion_id=datos.ubicacion_id,
        vendedor_id=vendedor_id,
        tipo_pago=datos.tipo_pago,
        estado=estado,
        observaciones=datos.observaciones.strip(),
    )
    detalles = [
        DetalleVenta(
            negocio_id=negocio_id,
            venta_id=venta.id,
            producto_id=linea.producto_id,
            cantidad=linea.cantidad,
            precio_unitario=productos[linea.producto_id].precio_venta,
        )
        for linea in datos.lineas
    ]
    DetalleVenta.objects.bulk_create(detalles)
    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=linea.producto_id, cantidad=linea.cantidad) for linea in datos.lineas],
        ubicacion_id=datos.ubicacion_id,
        referencia_tipo=MovimientoInventario.ReferenciaTipo.VENTA,
        referencia_id=venta.id,
        usuario_id=vendedor_id,
        negocio_id=negocio_id,
    )
    total = sum((detalle.cantidad * detalle.precio_unitario for detalle in detalles), Decimal("0"))
    if datos.tipo_pago == Venta.TipoPago.CONTADO:
        PagoVenta.objects.create(
            negocio_id=negocio_id,
            venta=venta,
            monto=total,
            metodo=datos.metodo_pago,
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
def registrar_abono(*, cuenta_id: int, monto: Decimal, metodo: str, recibido_por_id: int, negocio_id: int, referencia_transaccion: str = "") -> CuentaPorCobrar:
    """Registra un abono sin permitir que supere el saldo pendiente."""
    cuenta = CuentaPorCobrar.objects.select_for_update().select_related("venta").filter(
        pk=cuenta_id, negocio_id=negocio_id
    ).first()
    if cuenta is None:
        raise ValueError("La cuenta por cobrar no existe.")
    if monto <= 0 or monto > cuenta.saldo:
        raise ValueError("El abono debe ser mayor que cero y no superar el saldo.")
    nuevo_saldo = cuenta.saldo - monto
    PagoVenta.objects.create(
        negocio_id=negocio_id,
        venta=cuenta.venta,
        cuenta_por_cobrar=cuenta,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )
    cuenta.saldo = nuevo_saldo
    cuenta.estado = CuentaPorCobrar.Estado.PAGADA if nuevo_saldo == 0 else CuentaPorCobrar.Estado.PARCIAL
    cuenta.save(update_fields=["saldo", "estado", "actualizado_en"])
    return cuenta

"""Reglas de importes, estado del cliente y anulación de ventas."""

from decimal import Decimal

import pytest

from catalogo.models import Impuesto
from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from inventario.models import Existencia
from negocios.selectores.informes import resumen_de_ventas
from ventas.dtos import DatosDeVentaDTO, LineaDeVentaDTO
from ventas.models import MetodoPago, PagoVenta, Venta
from ventas.servicios import anular_venta, registrar_venta

pytestmark = pytest.mark.django_db


def preparar_venta(*, negocio, porcentaje_iva=Decimal("10.00")):
    impuesto = Impuesto.objects.create(
        negocio=negocio,
        nombre=f"IVA {porcentaje_iva}%",
        porcentaje=porcentaje_iva,
    )
    producto = FabricaDeProducto(
        negocio=negocio,
        impuesto=impuesto,
        precio_venta=Decimal("110.00"),
    )
    Existencia.objects.create(
        negocio=negocio,
        producto=producto,
        cantidad_disponible=Decimal("5.00"),
    )
    metodo_pago = MetodoPago.objects.create(negocio=negocio, nombre="Efectivo")
    datos = DatosDeVentaDTO(
        lineas=[LineaDeVentaDTO(producto_id=producto.id, cantidad=Decimal("1"))],
        tipo_pago=Venta.TipoPago.CONTADO,
        metodo_pago_id=metodo_pago.id,
    )
    return producto, datos


def test_precio_de_venta_con_iva_incluido_no_se_cobra_dos_veces(negocio, cajero):
    producto, datos = preparar_venta(negocio=negocio)

    venta = registrar_venta(
        datos=datos,
        negocio_id=negocio.id,
        vendedor_id=cajero.id,
    )
    detalle = venta.detalles.get()
    pago = venta.pagos.get()

    assert venta.subtotal == Decimal("100.00")
    assert venta.total_iva == Decimal("10.00")
    assert venta.total == producto.precio_venta == Decimal("110.00")
    assert detalle.subtotal == Decimal("110.00")
    assert pago.monto == Decimal("110.00")


def test_no_se_puede_vender_a_un_cliente_inactivo(negocio, cajero):
    _, datos = preparar_venta(negocio=negocio)
    cliente = FabricaDeCliente(negocio=negocio, activo=False)
    datos = DatosDeVentaDTO(
        lineas=datos.lineas,
        tipo_pago=datos.tipo_pago,
        metodo_pago_id=datos.metodo_pago_id,
        cliente_id=cliente.id,
    )

    with pytest.raises(ValueError, match="cliente no pertenece al negocio o está inactivo"):
        registrar_venta(
            datos=datos,
            negocio_id=negocio.id,
            vendedor_id=cajero.id,
        )

    assert Venta.objects.count() == 0


def test_anular_venta_marca_el_pago_de_contado_como_anulado(negocio, cajero):
    _, datos = preparar_venta(negocio=negocio, porcentaje_iva=Decimal("0"))
    venta = registrar_venta(
        datos=datos,
        negocio_id=negocio.id,
        vendedor_id=cajero.id,
    )
    pago = venta.pagos.get()

    anular_venta(
        venta_id=venta.id,
        negocio_id=negocio.id,
        usuario_id=cajero.id,
    )
    pago.refresh_from_db()
    venta.refresh_from_db()

    assert pago.estado == PagoVenta.Estado.ANULADO
    assert venta.estado == Venta.Estado.ANULADA
    assert resumen_de_ventas(negocio_id=negocio.id)["cobrado_total"] == Decimal("0")

"""Reglas de importes, estado del cliente y anulación de ventas."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from catalogo.models import Impuesto
from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from inventario.models import Existencia
from ventas.dtos import DatosDeVentaDTO, LineaDeVentaDTO
from ventas.models import MetodoPago, PagoVenta, Venta
from ventas.servicios import anular_venta, confirmar_entrega, registrar_abono, registrar_venta

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


def crear_venta_credito(*, negocio, cajero, cliente):
    _, datos = preparar_venta(negocio=negocio, porcentaje_iva=Decimal("0"))
    datos = DatosDeVentaDTO(
        lineas=datos.lineas,
        tipo_pago=Venta.TipoPago.CREDITO,
        cliente_id=cliente.id,
        fecha_vencimiento=timezone.localdate() + timedelta(days=30),
        metodo_pago_id=datos.metodo_pago_id,
    )
    venta = registrar_venta(
        datos=datos,
        negocio_id=negocio.id,
        vendedor_id=cajero.id,
    )
    return venta, datos


def test_no_anular_venta_de_contado_con_pago_confirmado(negocio, cajero):
    _, datos = preparar_venta(negocio=negocio, porcentaje_iva=Decimal("0"))
    venta = registrar_venta(datos=datos, negocio_id=negocio.id, vendedor_id=cajero.id)
    pago = venta.pagos.get()

    with pytest.raises(ValueError, match="pagos o abonos confirmados"):
        anular_venta(venta_id=venta.id, negocio_id=negocio.id, usuario_id=cajero.id)

    pago.refresh_from_db()
    venta.refresh_from_db()
    assert pago.estado == PagoVenta.Estado.CONFIRMADO
    assert venta.estado == Venta.Estado.PAGADA


def test_no_anular_venta_con_abono_parcial_y_exponer_estado_en_listado(
    negocio, cajero, cliente_api_autenticado
):
    cliente = FabricaDeCliente(negocio=negocio)
    venta, datos = crear_venta_credito(negocio=negocio, cajero=cajero, cliente=cliente)
    cuenta = venta.cuenta_por_cobrar
    registrar_abono(
        cuenta_id=cuenta.id,
        monto=Decimal("10.00"),
        metodo_pago_id=datos.metodo_pago_id,
        recibido_por_id=cajero.id,
        negocio_id=negocio.id,
    )

    with pytest.raises(ValueError, match="pagos o abonos confirmados"):
        anular_venta(venta_id=venta.id, negocio_id=negocio.id, usuario_id=cajero.id)

    respuesta = cliente_api_autenticado(cajero).get("/api/v1/ventas/")
    venta_listada = next(item for item in respuesta.data if item["id"] == venta.id)
    assert venta_listada["estado_pago"] == "PARCIAL"

    detalle = cliente_api_autenticado(cajero).get(f"/api/v1/ventas/{venta.id}/")
    assert detalle.data["estado_pago"] == "PARCIAL"
    assert detalle.data["puede_anular"] is False


def test_no_anular_venta_a_credito_totalmente_pagada(negocio, cajero):
    cliente = FabricaDeCliente(negocio=negocio)
    venta, datos = crear_venta_credito(negocio=negocio, cajero=cajero, cliente=cliente)
    cuenta = venta.cuenta_por_cobrar
    registrar_abono(
        cuenta_id=cuenta.id,
        monto=cuenta.total,
        metodo_pago_id=datos.metodo_pago_id,
        recibido_por_id=cajero.id,
        negocio_id=negocio.id,
    )

    with pytest.raises(ValueError, match="pagos o abonos confirmados"):
        anular_venta(venta_id=venta.id, negocio_id=negocio.id, usuario_id=cajero.id)


def test_no_anular_venta_ya_entregada(negocio, cajero):
    cliente = FabricaDeCliente(negocio=negocio)
    venta, _ = crear_venta_credito(negocio=negocio, cajero=cajero, cliente=cliente)
    confirmar_entrega(venta_id=venta.id, negocio_id=negocio.id)

    with pytest.raises(ValueError, match="pendientes de entrega"):
        anular_venta(venta_id=venta.id, negocio_id=negocio.id, usuario_id=cajero.id)

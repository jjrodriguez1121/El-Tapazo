"""Pruebas de las reglas de las fichas de cliente."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from clientes.dtos import DatosDeClienteDTO
from clientes.excepciones import DocumentoDuplicado, FechaDeNacimientoInvalida
from clientes.models import Cliente
from clientes.pruebas.fabricas import FabricaDeCliente
from clientes.selectores import historial_de_consumo
from clientes.servicios import clientes as servicio
from eventos.models import PedidoEvento
from eventos.pruebas.fabricas import (
    FabricaDeCuenta,
    FabricaDeDetallePedidoEvento,
    FabricaDePedidoEvento,
)
from nucleo.excepciones import NoEncontradoEnEsteNegocio

pytestmark = pytest.mark.django_db


def _datos(numero: str = "1020304050", nacimiento: date = date(1995, 6, 15)) -> DatosDeClienteDTO:
    return DatosDeClienteDTO(
        tipo_documento=Cliente.TipoDocumento.CEDULA,
        numero_documento=numero,
        nombre="Ana",
        apellido="Pérez",
        fecha_nacimiento=nacimiento,
    )


def test_registrar_un_cliente_guarda_su_ficha(negocio):
    cliente = servicio.registrar_cliente(negocio_id=negocio.id, datos=_datos())

    assert cliente.pk is not None
    assert cliente.nombre_completo == "Ana Pérez"


def test_un_menor_de_edad_se_registra_igual_y_solo_avisa(negocio):
    """Decisión 7: avisa, no bloquea. Quien decide si se le vende es la barra."""
    hace_dieciseis_anos = timezone.localdate() - timedelta(days=365 * 16)

    cliente = servicio.registrar_cliente(
        negocio_id=negocio.id, datos=_datos(nacimiento=hace_dieciseis_anos)
    )

    assert cliente.pk is not None
    assert cliente.es_menor_de_edad is True


def test_quien_ya_cumplio_dieciocho_no_es_menor(negocio):
    hace_veinte_anos = timezone.localdate() - timedelta(days=365 * 20)

    cliente = servicio.registrar_cliente(
        negocio_id=negocio.id, datos=_datos(nacimiento=hace_veinte_anos)
    )

    assert cliente.es_menor_de_edad is False


def test_una_fecha_de_nacimiento_del_futuro_no_pasa(negocio):
    manana = timezone.localdate() + timedelta(days=1)

    with pytest.raises(FechaDeNacimientoInvalida):
        servicio.registrar_cliente(negocio_id=negocio.id, datos=_datos(nacimiento=manana))


def test_no_se_repite_el_documento_dentro_del_mismo_negocio(negocio):
    """Es lo que evita el «Juan», «Juan P» y «Juan Perez» como tres personas."""
    servicio.registrar_cliente(negocio_id=negocio.id, datos=_datos())

    with pytest.raises(DocumentoDuplicado):
        servicio.registrar_cliente(negocio_id=negocio.id, datos=_datos())


def test_dos_negocios_pueden_tener_al_mismo_cliente(negocio):
    ajeno = FabricaDeCliente()

    propio = servicio.registrar_cliente(
        negocio_id=negocio.id, datos=_datos(numero=ajeno.numero_documento)
    )

    assert propio.numero_documento == ajeno.numero_documento


def test_actualizar_deja_conservar_el_propio_documento(negocio):
    cliente = servicio.registrar_cliente(negocio_id=negocio.id, datos=_datos())

    actualizado = servicio.actualizar_cliente(
        cliente_id=cliente.id, negocio_id=negocio.id, datos=_datos()
    )

    assert actualizado.numero_documento == "1020304050"


def test_desactivar_una_ficha_no_la_borra(negocio):
    """Borrarla dejaría huérfanas sus cuentas y comandas."""
    cliente = FabricaDeCliente(negocio=negocio)

    servicio.desactivar_cliente(cliente_id=cliente.id, negocio_id=negocio.id)

    cliente.refresh_from_db()
    assert cliente.activo is False


def test_no_se_puede_tocar_la_ficha_de_otro_negocio(negocio):
    ajena = FabricaDeCliente()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        servicio.desactivar_cliente(cliente_id=ajena.id, negocio_id=negocio.id)


# --------------------------------------------------------------------------- #
# Historial de consumo
# --------------------------------------------------------------------------- #
# La suma va aquí y no en las pruebas de API porque es la parte delicada: la
# multiplica la base de datos, y una expresión mixta sin `output_field` o con
# los dígitos justos falla — y es el número que ve el cliente al pagar.
def test_el_historial_suma_lo_consumido_en_cada_cuenta(negocio):
    cuenta = FabricaDeCuenta(negocio=negocio)
    pedido = FabricaDePedidoEvento(negocio=negocio, cliente_evento=cuenta)
    FabricaDeDetallePedidoEvento(
        negocio=negocio,
        pedido_evento=pedido,
        cantidad=Decimal("3.00"),
        precio_unitario=Decimal("5000.00"),
    )
    FabricaDeDetallePedidoEvento(
        negocio=negocio,
        pedido_evento=pedido,
        cantidad=Decimal("2.00"),
        precio_unitario=Decimal("8000.00"),
    )

    historial = historial_de_consumo(cliente_id=cuenta.cliente_id, negocio_id=negocio.id)

    assert len(historial) == 1
    assert historial[0].consumido == Decimal("31000.0000")
    assert PedidoEvento.objects.count() == 1


def test_una_comanda_cancelada_no_se_le_cobra(negocio):
    """Devolvió el producto al inventario: tampoco se le cobra."""
    cuenta = FabricaDeCuenta(negocio=negocio)
    servida = FabricaDePedidoEvento(negocio=negocio, cliente_evento=cuenta)
    cancelada = FabricaDePedidoEvento(
        negocio=negocio, cliente_evento=cuenta, estado=PedidoEvento.Estado.CANCELADO
    )
    FabricaDeDetallePedidoEvento(
        negocio=negocio,
        pedido_evento=servida,
        cantidad=Decimal("1.00"),
        precio_unitario=Decimal("5000.00"),
    )
    FabricaDeDetallePedidoEvento(
        negocio=negocio,
        pedido_evento=cancelada,
        cantidad=Decimal("10.00"),
        precio_unitario=Decimal("5000.00"),
    )

    historial = historial_de_consumo(cliente_id=cuenta.cliente_id, negocio_id=negocio.id)

    assert historial[0].consumido == Decimal("5000.0000")


def test_una_cuenta_sin_pedidos_consume_cero_y_no_nulo(negocio):
    cuenta = FabricaDeCuenta(negocio=negocio)

    historial = historial_de_consumo(cliente_id=cuenta.cliente_id, negocio_id=negocio.id)

    assert historial[0].consumido == Decimal("0")

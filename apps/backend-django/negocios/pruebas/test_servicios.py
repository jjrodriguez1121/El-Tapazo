"""Pruebas de la administración de negocios y del resumen por canal.

Lo que importa aquí son dos cosas: que suspender y reactivar no se puedan
repetir en silencio, y que el resumen sume cada canal por separado sin
mezclarlos.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from distribucion.dtos import LineaDePedidoDTO
from distribucion.pruebas.fabricas import FabricaDeClienteDistribucion
from distribucion.servicios import pagos as pagos_de_mayoreo
from distribucion.servicios import pedidos as pedidos_de_mayoreo
from eventos.dtos import LineaDePedidoDTO as LineaDeComandaDTO
from eventos.servicios import cuentas, jornadas
from eventos.servicios import pedidos as comandas
from inventario.pruebas.fabricas import FabricaDeExistencia
from negocios.excepciones import (
    NegocioNoEncontrado,
    NegocioYaActivo,
    NegocioYaSuspendido,
    NitDeNegocioDuplicado,
    RangoDeFechasInvalido,
)
from negocios.models import Negocio
from negocios.pruebas.fabricas import FabricaDeNegocio
from negocios.selectores import negocio_del_usuario, resumen_de_ventas
from negocios.servicios import negocios as servicio

pytestmark = pytest.mark.django_db


@pytest.fixture
def bodega(negocio):
    """Cien cervezas: 5.000 en la barra, 3.500 al por mayor."""
    return FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(
            negocio=negocio,
            precio_evento=Decimal("5000.00"),
            precio_mayorista=Decimal("3500.00"),
        ),
    )


def _vender_en_la_barra(negocio, bodega, mesero, cantidad="2.00"):
    """Una comanda de mostrador: descuenta y deja su importe en el canal bar."""
    jornada = jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=bodega.ubicacion_id
    )
    return comandas.registrar_pedido(
        evento_id=jornada.id,
        cliente_evento_id=None,
        lineas=[LineaDeComandaDTO(producto_id=bodega.producto_id, cantidad=Decimal(cantidad))],
        mesero_id=mesero.id,
        negocio_id=negocio.id,
    )


def _vender_al_por_mayor(negocio, bodega, administrador, cantidad="10.00"):
    tienda = FabricaDeClienteDistribucion(negocio=negocio)
    return pedidos_de_mayoreo.crear_pedido(
        cliente_distribucion_id=tienda.id,
        lineas=[LineaDePedidoDTO(producto_id=bodega.producto_id, cantidad=Decimal(cantidad))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )


# --------------------------------------------------------------------------- #
# Alta y cambio de datos
# --------------------------------------------------------------------------- #
def test_crear_negocio_lo_deja_activo():
    creado = servicio.crear_negocio(nombre_comercial="Bar El Tapaso", nit="900999888")

    assert creado.estado == Negocio.Estado.ACTIVO
    assert creado.esta_operativo


def test_un_negocio_nace_sin_nadie_dentro():
    """Su primer administrador se invita después, desde la terminal."""
    creado = servicio.crear_negocio(nombre_comercial="Bar El Tapaso", nit="900999888")

    assert not creado.usuarios.exists()


def test_no_hay_dos_negocios_con_el_mismo_nit():
    """El NIT es único global: dos filas con el mismo NIT son el mismo negocio."""
    servicio.crear_negocio(nombre_comercial="Bar El Tapaso", nit="900999888")

    with pytest.raises(NitDeNegocioDuplicado):
        servicio.crear_negocio(nombre_comercial="Otro nombre", nit="900999888")


def test_actualizar_los_datos_de_un_negocio(negocio):
    actualizado = servicio.actualizar_datos(
        negocio_id=negocio.id, nombre_comercial="  Bar Nuevo  ", nit="900111222"
    )

    assert actualizado.nombre_comercial == "Bar Nuevo"
    assert actualizado.nit == "900111222"


def test_actualizar_con_el_nit_de_otro_negocio_falla(negocio):
    otro = FabricaDeNegocio()

    with pytest.raises(NitDeNegocioDuplicado):
        servicio.actualizar_datos(
            negocio_id=negocio.id, nombre_comercial=negocio.nombre_comercial, nit=otro.nit
        )


def test_un_negocio_que_no_existe_da_no_encontrado():
    with pytest.raises(NegocioNoEncontrado):
        servicio.suspender_negocio(negocio_id=999999)


# --------------------------------------------------------------------------- #
# Suspensión y reactivación
# --------------------------------------------------------------------------- #
def test_suspender_un_negocio(negocio):
    suspendido = servicio.suspender_negocio(negocio_id=negocio.id)

    assert suspendido.estado == Negocio.Estado.SUSPENDIDO
    assert not suspendido.esta_operativo


def test_suspender_dos_veces_avisa(negocio):
    servicio.suspender_negocio(negocio_id=negocio.id)

    with pytest.raises(NegocioYaSuspendido):
        servicio.suspender_negocio(negocio_id=negocio.id)


def test_reactivar_devuelve_el_negocio_a_la_operacion(negocio):
    servicio.suspender_negocio(negocio_id=negocio.id)

    reactivado = servicio.reactivar_negocio(negocio_id=negocio.id)

    assert reactivado.esta_operativo


def test_reactivar_lo_que_nunca_se_suspendio_avisa(negocio):
    with pytest.raises(NegocioYaActivo):
        servicio.reactivar_negocio(negocio_id=negocio.id)


def test_suspender_no_borra_nada(negocio, bodega, administrador):
    """La diferencia entre suspender y dar de baja: los datos siguen ahí."""
    _vender_al_por_mayor(negocio, bodega, administrador)

    servicio.suspender_negocio(negocio_id=negocio.id)

    assert negocio.pedidos_distribucion.count() == 1
    assert negocio.usuarios.count() >= 1


# --------------------------------------------------------------------------- #
# El negocio de quien pregunta
# --------------------------------------------------------------------------- #
def test_el_negocio_del_usuario_es_el_suyo(negocio, mesero):
    assert negocio_del_usuario(usuario_id=mesero.id).id == negocio.id


def test_el_staff_no_tiene_negocio(staff):
    """Existe por encima de todos, así que no hay ninguno que devolverle."""
    with pytest.raises(NegocioNoEncontrado):
        negocio_del_usuario(usuario_id=staff.id)


# --------------------------------------------------------------------------- #
# Resumen de ventas por canal
# --------------------------------------------------------------------------- #
def test_el_resumen_separa_los_dos_canales(negocio, bodega, mesero, administrador):
    _vender_en_la_barra(negocio, bodega, mesero)  # 2 × 5.000
    _vender_al_por_mayor(negocio, bodega, administrador)  # 10 × 3.500

    resumen = resumen_de_ventas(negocio_id=negocio.id)

    por_canal = {canal["canal"]: canal for canal in resumen["canales"]}
    assert por_canal["bar"]["vendido"] == Decimal("10000.00")
    assert por_canal["mayoreo"]["vendido"] == Decimal("35000.00")
    assert resumen["vendido_total"] == Decimal("45000.00")


def test_lo_vendido_y_lo_cobrado_no_son_lo_mismo(negocio, bodega, administrador):
    """El mayoreo va a crédito: se factura hoy y se cobra el mes que viene."""
    pedido = _vender_al_por_mayor(negocio, bodega, administrador)
    pagos_de_mayoreo.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("10000.00"),
        metodo="transferencia",
        recibido_por_id=administrador.id,
    )

    resumen = resumen_de_ventas(negocio_id=negocio.id)

    assert resumen["vendido_total"] == Decimal("35000.00")
    assert resumen["cobrado_total"] == Decimal("10000.00")


def test_una_comanda_cancelada_no_cuenta_como_venta(negocio, bodega, mesero, cajero):
    comanda = _vender_en_la_barra(negocio, bodega, mesero)
    comandas.cancelar_pedido(
        pedido_id=comanda.id,
        negocio_id=negocio.id,
        usuario_id=cajero.id,
        motivo="Se equivocó el mesero.",
    )

    assert resumen_de_ventas(negocio_id=negocio.id)["vendido_total"] == Decimal("0.00")


def test_el_resumen_no_ve_lo_de_otro_negocio(negocio, bodega, administrador):
    _vender_al_por_mayor(negocio, bodega, administrador)
    otro = FabricaDeNegocio()

    assert resumen_de_ventas(negocio_id=otro.id)["vendido_total"] == Decimal("0.00")


def test_fuera_del_rango_no_se_cuenta(negocio, bodega, administrador):
    _vender_al_por_mayor(negocio, bodega, administrador)
    ayer = timezone.localdate() - timedelta(days=1)

    resumen = resumen_de_ventas(negocio_id=negocio.id, desde=ayer - timedelta(days=7), hasta=ayer)

    assert resumen["vendido_total"] == Decimal("0.00")


def test_sin_fechas_el_resumen_es_del_mes_en_curso(negocio):
    resumen = resumen_de_ventas(negocio_id=negocio.id)

    hoy = timezone.localdate()
    assert resumen["desde"] == hoy.replace(day=1)
    assert resumen["hasta"] == hoy


def test_un_rango_al_reves_se_rechaza(negocio):
    hoy = timezone.localdate()

    with pytest.raises(RangoDeFechasInvalido):
        resumen_de_ventas(negocio_id=negocio.id, desde=hoy, hasta=hoy - timedelta(days=3))


def test_la_cuenta_de_una_persona_tambien_suma_al_canal_bar(negocio, bodega, mesero):
    """No solo el mostrador: lo de una cuenta con pulsera es la misma venta."""
    jornada = jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=bodega.ubicacion_id
    )
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    cuenta = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )
    comandas.registrar_pedido(
        evento_id=jornada.id,
        cliente_evento_id=cuenta.id,
        lineas=[LineaDeComandaDTO(producto_id=bodega.producto_id, cantidad=Decimal("3.00"))],
        mesero_id=mesero.id,
        negocio_id=negocio.id,
    )

    assert resumen_de_ventas(negocio_id=negocio.id)["vendido_total"] == Decimal("15000.00")

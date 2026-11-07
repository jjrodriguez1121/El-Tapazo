"""Pruebas del canal evento/bar.

Lo que más importa aquí son tres cosas: que vender descuente de verdad, que
cobrar no se pueda hacer dos veces, y que cancelar devuelva exactamente lo que
se descontó.
"""

from decimal import Decimal

import pytest
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from eventos.dtos import LineaDePedidoDTO
from eventos.excepciones import (
    CuentasSinSaldar,
    CuentaYaLiberada,
    EventoSinUbicacion,
    GrupoCerrado,
    JornadaNoAbierta,
    MotivoObligatorio,
    PagoNoCubreElConsumo,
    PedidoNoCancelable,
    PedidoSinLineas,
    PulseraYaAsignada,
)
from eventos.models import AlertaConsumo, Evento, GrupoEvento, PagoEvento, PedidoEvento
from eventos.pruebas.fabricas import FabricaDeCuenta, FabricaDeEvento, FabricaDePulsera
from eventos.selectores import consumo_de_una_cuenta, informe_de_cierre
from eventos.servicios import alertas, cuentas, jornadas, pagos, pedidos, pulseras
from inventario.models import Existencia, MovimientoInventario
from inventario.pruebas.fabricas import FabricaDeExistencia, FabricaDeUbicacion
from nucleo.excepciones import NoEncontradoEnEsteNegocio

pytestmark = pytest.mark.django_db

METODO = PagoEvento.Metodo.EFECTIVO


@pytest.fixture
def barra(negocio):
    """Una ubicación con cien cervezas a 5000, lista para vender."""
    return FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(negocio=negocio, precio_evento=Decimal("5000.00")),
    )


@pytest.fixture
def jornada(negocio, barra):
    return jornadas.obtener_o_abrir_jornada(negocio_id=negocio.id, ubicacion_id=barra.ubicacion_id)


@pytest.fixture
def cuenta(negocio, jornada, mesero):
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id, mesa_zona="Mesa 1"
    )
    return cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )


def _pedir(negocio, jornada, mesero, barra, cuenta_id, cantidad="2.00"):
    return pedidos.registrar_pedido(
        evento_id=jornada.id,
        cliente_evento_id=cuenta_id,
        lineas=[LineaDePedidoDTO(producto_id=barra.producto_id, cantidad=Decimal(cantidad))],
        mesero_id=mesero.id,
        negocio_id=negocio.id,
    )


# --------------------------------------------------------------------------- #
# Apertura automática de la jornada
# --------------------------------------------------------------------------- #
def test_la_primera_llamada_abre_la_jornada_y_la_segunda_la_reutiliza(negocio, barra):
    """Nadie tiene que crear el evento a mano cada mañana."""
    primera = jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=barra.ubicacion_id
    )
    segunda = jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=barra.ubicacion_id
    )

    assert primera.id == segunda.id
    assert primera.estado == Evento.Estado.EN_CURSO
    assert Evento.objects.count() == 1


def test_la_jornada_se_llama_por_la_fecha_local(negocio, barra):
    """Con `date.today()` una barra que abre a las once partiría la noche en dos."""
    jornada = jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=barra.ubicacion_id
    )

    assert jornada.nombre.startswith(f"Jornada del {timezone.localdate().day} de ")


def test_no_se_abre_jornada_en_la_ubicacion_de_otro_negocio(negocio):
    ajena = FabricaDeUbicacion()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        jornadas.obtener_o_abrir_jornada(negocio_id=negocio.id, ubicacion_id=ajena.id)


def test_cerrar_la_caja_con_una_cuenta_abierta_falla_y_dice_cual(negocio, jornada, cuenta):
    """Decisión 9. La lista va en los detalles para que la pantalla la pinte."""
    with pytest.raises(CuentasSinSaldar) as error:
        jornadas.cerrar_jornada(evento_id=jornada.id, negocio_id=negocio.id)

    assert error.value.detalles["cuentas"][0]["cuenta_id"] == cuenta.id


def test_cerrar_la_caja_sin_cuentas_abiertas_pasa(negocio, jornada):
    cerrada = jornadas.cerrar_jornada(evento_id=jornada.id, negocio_id=negocio.id)

    assert cerrada.estado == Evento.Estado.CERRADO
    assert cerrada.fecha_fin is not None


# --------------------------------------------------------------------------- #
# Cuentas y pulseras
# --------------------------------------------------------------------------- #
def test_una_pulsera_no_se_asigna_a_dos_personas_a_la_vez(negocio, jornada, mesero):
    pulsera = FabricaDePulsera(negocio=negocio)
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )

    with pytest.raises(PulseraYaAsignada):
        cuentas.abrir_cuenta(
            grupo_id=grupo.id,
            cliente_id=FabricaDeCliente(negocio=negocio).id,
            negocio_id=negocio.id,
            asignada_por_id=mesero.id,
            pulsera_id=pulsera.id,
        )


def test_liberar_una_cuenta_deja_la_pulsera_libre_para_otra_fila(negocio, jornada, mesero, cajero):
    """El borrado ocurre en la base, no en el chip."""
    pulsera = FabricaDePulsera(negocio=negocio)
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    primera = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )
    cuentas.liberar_cuenta(cuenta_id=primera.id, negocio_id=negocio.id, liberada_por_id=cajero.id)

    segunda = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )

    assert segunda.id != primera.id
    assert segunda.pulsera_id == pulsera.id


def test_una_cuenta_liberada_no_se_libera_dos_veces(negocio, cuenta, cajero):
    cuentas.liberar_cuenta(cuenta_id=cuenta.id, negocio_id=negocio.id, liberada_por_id=cajero.id)

    with pytest.raises(CuentaYaLiberada):
        cuentas.liberar_cuenta(
            cuenta_id=cuenta.id, negocio_id=negocio.id, liberada_por_id=cajero.id
        )


def test_un_menor_de_edad_abre_cuenta_igual(negocio, jornada, mesero):
    """Decisión 7: avisa, no bloquea."""
    menor = FabricaDeCliente(negocio=negocio, fecha_nacimiento=timezone.localdate())
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )

    abierta = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=menor.id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )

    assert abierta.pk is not None
    assert abierta.cliente.es_menor_de_edad is True


def test_cerrar_el_grupo_libera_las_cuentas_que_seguian_abiertas(negocio, jornada, cuenta, cajero):
    cuentas.cerrar_grupo(
        grupo_id=cuenta.grupo_evento_id, negocio_id=negocio.id, cerrado_por_id=cajero.id
    )

    cuenta.refresh_from_db()
    assert cuenta.liberada_en is not None
    assert GrupoEvento.objects.get(pk=cuenta.grupo_evento_id).estado == (GrupoEvento.Estado.CERRADO)


def test_no_se_abre_una_cuenta_en_un_grupo_cerrado(negocio, cuenta, cajero):
    cuentas.cerrar_grupo(
        grupo_id=cuenta.grupo_evento_id, negocio_id=negocio.id, cerrado_por_id=cajero.id
    )

    with pytest.raises(GrupoCerrado):
        cuentas.abrir_cuenta(
            grupo_id=cuenta.grupo_evento_id,
            cliente_id=FabricaDeCliente(negocio=negocio).id,
            negocio_id=negocio.id,
            asignada_por_id=cajero.id,
        )


# --------------------------------------------------------------------------- #
# La venta
# --------------------------------------------------------------------------- #
def test_tomar_una_comanda_descuenta_el_stock_y_congela_el_precio(
    negocio, jornada, mesero, barra, cuenta
):
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="3.00")

    barra.refresh_from_db()
    detalle = pedido.detalles.get()
    assert barra.cantidad_disponible == Decimal("97.00")
    assert detalle.precio_unitario == Decimal("5000.00")
    assert MovimientoInventario.objects.get().cantidad == Decimal("-3.00")


def test_subir_el_precio_manana_no_cambia_la_comanda_de_hoy(
    negocio, jornada, mesero, barra, cuenta
):
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id)
    barra.producto.precio_evento = Decimal("9000.00")
    barra.producto.save(update_fields=["precio_evento"])

    assert pedido.detalles.get().precio_unitario == Decimal("5000.00")
    assert consumo_de_una_cuenta(cliente_evento_id=cuenta.id, negocio_id=negocio.id) == Decimal(
        "10000.00"
    )


def test_vender_sin_stock_no_deja_ni_el_pedido(negocio, jornada, mesero, barra, cuenta):
    """Decisiones 1 y 2: se bloquea siempre, y media comanda es peor que ninguna."""
    from inventario.excepciones import ExistenciasInsuficientes

    with pytest.raises(ExistenciasInsuficientes):
        _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="500.00")

    assert PedidoEvento.objects.count() == 0
    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("100.00")


def test_la_venta_de_mostrador_no_necesita_cuenta(negocio, jornada, mesero, barra):
    pedido = _pedir(negocio, jornada, mesero, barra, None)

    assert pedido.cliente_evento_id is None
    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("98.00")


def test_una_comanda_sin_lineas_no_es_una_comanda(negocio, jornada, mesero):
    with pytest.raises(PedidoSinLineas):
        pedidos.registrar_pedido(
            evento_id=jornada.id,
            cliente_evento_id=None,
            lineas=[],
            mesero_id=mesero.id,
            negocio_id=negocio.id,
        )


def test_no_se_vende_con_el_producto_de_otro_negocio(negocio, jornada, mesero):
    ajeno = FabricaDeProducto()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        pedidos.registrar_pedido(
            evento_id=jornada.id,
            cliente_evento_id=None,
            lineas=[LineaDePedidoDTO(producto_id=ajeno.id, cantidad=Decimal("1.00"))],
            mesero_id=mesero.id,
            negocio_id=negocio.id,
        )


def test_no_se_vende_en_un_evento_sin_ubicacion(negocio, mesero, barra):
    """No hay de dónde descontar."""
    planeado = FabricaDeEvento(negocio=negocio, ubicacion=None, estado=Evento.Estado.EN_CURSO)

    with pytest.raises(EventoSinUbicacion):
        pedidos.registrar_pedido(
            evento_id=planeado.id,
            cliente_evento_id=None,
            lineas=[LineaDePedidoDTO(producto_id=barra.producto_id, cantidad=Decimal("1.00"))],
            mesero_id=mesero.id,
            negocio_id=negocio.id,
        )


def test_no_se_vende_en_una_jornada_cerrada(negocio, jornada, mesero, barra):
    jornadas.cerrar_jornada(evento_id=jornada.id, negocio_id=negocio.id)

    with pytest.raises(JornadaNoAbierta):
        _pedir(negocio, jornada, mesero, barra, None)


# --------------------------------------------------------------------------- #
# Cancelar
# --------------------------------------------------------------------------- #
def test_cancelar_devuelve_exactamente_lo_que_descontó(
    negocio, jornada, mesero, cajero, barra, cuenta
):
    """Decisión 1: cada comanda cancelada devuelve lo que quitó, ni más ni menos."""
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="4.00")

    pedidos.cancelar_pedido(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=cajero.id,
        motivo="Se equivocó de mesa.",
    )

    barra.refresh_from_db()
    pedido.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("100.00")
    assert pedido.estado == PedidoEvento.Estado.CANCELADO


def test_una_comanda_entregada_se_puede_cancelar(negocio, jornada, mesero, cajero, barra, cuenta):
    """Decisión 11: en una barra los errores se detectan después de servir."""
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id)
    pedidos.entregar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    pedidos.cancelar_pedido(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=cajero.id,
        motivo="Estaba caliente.",
    )

    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("100.00")


def test_una_comanda_ya_cobrada_no_se_cancela(negocio, jornada, mesero, cajero, barra, cuenta):
    """Devolver el dinero es otra operación."""
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id)
    pagos.registrar_pago_de_cuenta(
        cuenta_id=cuenta.id,
        negocio_id=negocio.id,
        monto=Decimal("10000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    with pytest.raises(PedidoNoCancelable):
        pedidos.cancelar_pedido(
            pedido_id=pedido.id,
            negocio_id=negocio.id,
            usuario_id=cajero.id,
            motivo="Tarde.",
        )


def test_cancelar_sin_motivo_no_pasa(negocio, jornada, mesero, cajero, barra, cuenta):
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id)

    with pytest.raises(MotivoObligatorio):
        pedidos.cancelar_pedido(
            pedido_id=pedido.id, negocio_id=negocio.id, usuario_id=cajero.id, motivo="  "
        )


def test_cancelar_dos_veces_no_repone_de_mas(negocio, jornada, mesero, cajero, barra, cuenta):
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="4.00")
    pedidos.cancelar_pedido(
        pedido_id=pedido.id, negocio_id=negocio.id, usuario_id=cajero.id, motivo="Error."
    )

    with pytest.raises(PedidoNoCancelable):
        pedidos.cancelar_pedido(
            pedido_id=pedido.id, negocio_id=negocio.id, usuario_id=cajero.id, motivo="Otra."
        )

    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("100.00")


def test_lo_cancelado_no_se_le_cobra(negocio, jornada, mesero, cajero, barra, cuenta):
    servida = _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="2.00")
    cancelada = _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="10.00")
    pedidos.cancelar_pedido(
        pedido_id=cancelada.id, negocio_id=negocio.id, usuario_id=cajero.id, motivo="Error."
    )

    assert servida.pk is not None
    assert consumo_de_una_cuenta(cliente_evento_id=cuenta.id, negocio_id=negocio.id) == Decimal(
        "10000.00"
    )


# --------------------------------------------------------------------------- #
# Cobro
# --------------------------------------------------------------------------- #
def test_cobrar_la_cuenta_la_libera(negocio, jornada, mesero, cajero, barra, cuenta):
    _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="2.00")

    resultado = pagos.registrar_pago_de_cuenta(
        cuenta_id=cuenta.id,
        negocio_id=negocio.id,
        monto=Decimal("10000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    cuenta.refresh_from_db()
    assert resultado.consumido == Decimal("10000.00")
    assert cuenta.liberada_en is not None


def test_un_pago_que_no_cubre_lo_consumido_se_rechaza(
    negocio, jornada, mesero, cajero, barra, cuenta
):
    """Decisión 3: en el bar no hay abonos, se salda de una."""
    _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="2.00")

    with pytest.raises(PagoNoCubreElConsumo):
        pagos.registrar_pago_de_cuenta(
            cuenta_id=cuenta.id,
            negocio_id=negocio.id,
            monto=Decimal("5000.00"),
            metodo=METODO,
            recibido_por_id=cajero.id,
        )

    cuenta.refresh_from_db()
    assert cuenta.liberada_en is None


def test_no_se_cobra_dos_veces_la_misma_cuenta(negocio, jornada, mesero, cajero, barra, cuenta):
    """La restricción de la pulsera no cubre esto: impide dos asignaciones
    activas, no dos cierres."""
    _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="2.00")
    pagos.registrar_pago_de_cuenta(
        cuenta_id=cuenta.id,
        negocio_id=negocio.id,
        monto=Decimal("10000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    with pytest.raises(CuentaYaLiberada):
        pagos.registrar_pago_de_cuenta(
            cuenta_id=cuenta.id,
            negocio_id=negocio.id,
            monto=Decimal("10000.00"),
            metodo=METODO,
            recibido_por_id=cajero.id,
        )

    assert PagoEvento.objects.count() == 1


def test_cobrar_el_grupo_cierra_todas_sus_cuentas(negocio, jornada, mesero, cajero, barra):
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    primera = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )
    segunda = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )
    _pedir(negocio, jornada, mesero, barra, primera.id, cantidad="1.00")
    _pedir(negocio, jornada, mesero, barra, segunda.id, cantidad="2.00")

    resultado = pagos.registrar_pago_de_grupo(
        grupo_id=grupo.id,
        negocio_id=negocio.id,
        monto=Decimal("15000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    assert resultado.consumido == Decimal("15000.00")
    assert resultado.cuentas_liberadas == 2


def test_cobrar_una_venta_de_mostrador(negocio, jornada, mesero, cajero, barra):
    pedido = _pedir(negocio, jornada, mesero, barra, None, cantidad="2.00")

    resultado = pagos.registrar_pago_de_mostrador(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("10000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    assert resultado.consumido == Decimal("10000.00")


def test_una_comanda_de_cuenta_no_se_cobra_en_el_mostrador(
    negocio, jornada, mesero, cajero, barra, cuenta
):
    pedido = _pedir(negocio, jornada, mesero, barra, cuenta.id)

    with pytest.raises(PedidoNoCancelable):
        pagos.registrar_pago_de_mostrador(
            pedido_id=pedido.id,
            negocio_id=negocio.id,
            monto=Decimal("10000.00"),
            metodo=METODO,
            recibido_por_id=cajero.id,
        )


# --------------------------------------------------------------------------- #
# Alertas de consumo
# --------------------------------------------------------------------------- #
def test_cruzar_el_limite_crea_una_alerta_con_el_umbral_copiado(negocio, jornada, mesero, barra):
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    vigilada = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        limite_alerta=Decimal("8000.00"),
    )

    _pedir(negocio, jornada, mesero, barra, vigilada.id, cantidad="2.00")

    alerta = AlertaConsumo.objects.get()
    assert alerta.monto_acumulado == Decimal("10000.00")
    assert alerta.umbral_superado == Decimal("8000.00")


def test_no_se_repite_la_alerta_en_cada_comanda_posterior(negocio, jornada, mesero, barra):
    """Si no, la pantalla del cajero se llena de avisos de lo mismo."""
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    vigilada = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        limite_alerta=Decimal("8000.00"),
    )

    _pedir(negocio, jornada, mesero, barra, vigilada.id, cantidad="2.00")
    _pedir(negocio, jornada, mesero, barra, vigilada.id, cantidad="2.00")

    assert AlertaConsumo.objects.count() == 1


def test_una_cuenta_sin_limite_no_dispara_alertas(negocio, jornada, mesero, barra, cuenta):
    _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="10.00")

    assert AlertaConsumo.objects.count() == 0


def test_atender_una_alerta_guarda_quien_y_que_hizo(negocio, jornada, mesero, barra, cajero):
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    vigilada = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        limite_alerta=Decimal("1000.00"),
    )
    _pedir(negocio, jornada, mesero, barra, vigilada.id, cantidad="1.00")

    atendida = alertas.atender_alerta(
        alerta_id=AlertaConsumo.objects.get().id,
        negocio_id=negocio.id,
        atendida_por_id=cajero.id,
        accion_tomada="Se le cortó el servicio.",
    )

    assert atendida.atendida_en is not None
    assert atendida.atendida_por_id == cajero.id


# --------------------------------------------------------------------------- #
# Punto de control e informe de cierre
# --------------------------------------------------------------------------- #
def test_el_punto_de_control_responde_con_saldo_y_solo_el_nombre(negocio, jornada, mesero, barra):
    """Cualquiera con un lector barato puede preguntar: sale lo mínimo."""
    from eventos.selectores import consultar_punto_de_control

    pulsera = FabricaDePulsera(negocio=negocio)
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    con_pulsera = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )
    _pedir(negocio, jornada, mesero, barra, con_pulsera.id, cantidad="2.00")

    respuesta = consultar_punto_de_control(uid_tag=pulsera.uid_tag, negocio_id=negocio.id)

    assert respuesta["estado"] == "con_saldo"
    assert respuesta["monto"] == Decimal("10000.00")
    assert set(respuesta) == {"estado", "cliente", "monto"}


def test_el_punto_de_control_dice_saldada_si_ya_pago(negocio, jornada, mesero, cajero, barra):
    from eventos.selectores import consultar_punto_de_control

    pulsera = FabricaDePulsera(negocio=negocio)
    grupo = cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    con_pulsera = cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )
    _pedir(negocio, jornada, mesero, barra, con_pulsera.id, cantidad="1.00")
    pagos.registrar_pago_de_cuenta(
        cuenta_id=con_pulsera.id,
        negocio_id=negocio.id,
        monto=Decimal("5000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    respuesta = consultar_punto_de_control(uid_tag=pulsera.uid_tag, negocio_id=negocio.id)

    assert respuesta["estado"] == "saldada"


def test_el_informe_de_cierre_cuadra_lo_vendido_con_lo_cobrado(
    negocio, jornada, mesero, cajero, barra, cuenta
):
    _pedir(negocio, jornada, mesero, barra, cuenta.id, cantidad="3.00")
    pagos.registrar_pago_de_cuenta(
        cuenta_id=cuenta.id,
        negocio_id=negocio.id,
        monto=Decimal("15000.00"),
        metodo=METODO,
        recibido_por_id=cajero.id,
    )

    informe = informe_de_cierre(evento_id=jornada.id, negocio_id=negocio.id)

    assert informe["total_cobrado"] == Decimal("15000.00")
    assert informe["ventas_por_producto"][0]["unidades"] == Decimal("3.00")
    assert informe["cuentas_atendidas"] == 1


def test_registrar_una_pulsera_normaliza_el_uid(negocio):
    pulsera = pulseras.registrar_pulsera(negocio_id=negocio.id, uid_tag=" 04a2b3c4 ")

    assert pulsera.uid_tag == "04A2B3C4"


def test_no_se_ve_la_cuenta_de_otro_negocio(negocio, cajero):
    ajena = FabricaDeCuenta()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        cuentas.liberar_cuenta(cuenta_id=ajena.id, negocio_id=negocio.id, liberada_por_id=cajero.id)


def test_el_saldo_del_negocio_no_cambia_al_cancelar(negocio, jornada, mesero, cajero, barra):
    """La invariante que hereda del inventario."""
    antes = Existencia.objects.get(pk=barra.pk).cantidad_disponible
    pedido = _pedir(negocio, jornada, mesero, barra, None, cantidad="7.00")
    pedidos.cancelar_pedido(
        pedido_id=pedido.id, negocio_id=negocio.id, usuario_id=cajero.id, motivo="Error."
    )

    assert Existencia.objects.get(pk=barra.pk).cantidad_disponible == antes

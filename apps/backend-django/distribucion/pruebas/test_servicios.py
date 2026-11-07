"""Pruebas del canal mayorista.

Lo que más importa aquí son tres cosas: que el stock salga **al despachar** y
no antes, que un pedido que no se pudo entregar devuelva **exactamente** lo que
sacó y se pueda volver a despachar, y que los abonos nunca pasen del total.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from distribucion.dtos import DatosDeClienteDistribucionDTO, LineaDePedidoDTO
from distribucion.excepciones import (
    MotivoObligatorio,
    NitDuplicado,
    PagoSuperaElTotal,
    PedidoNoCancelable,
    PedidoNoCobrable,
    PedidoNoDespachable,
    PedidoNoEntregable,
    PedidoSinLineas,
)
from distribucion.models import PagoDistribucion, PedidoDistribucion
from distribucion.pruebas.fabricas import FabricaDeClienteDistribucion
from distribucion.selectores import (
    clientes_en_mora,
    obtener_pedido,
    saldo_de_un_cliente,
    saldo_de_un_pedido,
    total_de_un_pedido,
)
from distribucion.servicios import clientes as servicio_de_clientes
from distribucion.servicios import pagos, pedidos
from inventario.excepciones import ExistenciasInsuficientes
from inventario.models import Existencia, MovimientoInventario
from inventario.pruebas.fabricas import FabricaDeExistencia
from nucleo.excepciones import NoEncontradoEnEsteNegocio
from usuarios.pruebas.fabricas import FabricaDeAdministrador

pytestmark = pytest.mark.django_db

METODO = PagoDistribucion.Metodo.TRANSFERENCIA
REFERENCIA = MovimientoInventario.ReferenciaTipo.PEDIDO_DISTRIBUCION


@pytest.fixture
def bodega(negocio):
    """Una bodega con cien cervezas a 3.500 el mayorista."""
    return FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(negocio=negocio, precio_mayorista=Decimal("3500.00")),
    )


@pytest.fixture
def tienda(negocio):
    return FabricaDeClienteDistribucion(negocio=negocio, dias_credito=30)


def _pedir(negocio, tienda, bodega, administrador, cantidad="10.00"):
    return pedidos.crear_pedido(
        cliente_distribucion_id=tienda.id,
        lineas=[LineaDePedidoDTO(producto_id=bodega.producto_id, cantidad=Decimal(cantidad))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )


def _despachar(pedido, negocio, bodega, administrador):
    return pedidos.despachar_pedido(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        ubicacion_id=bodega.ubicacion_id,
        usuario_id=administrador.id,
    )


def _disponible(bodega) -> Decimal:
    return Existencia.objects.get(pk=bodega.pk).cantidad_disponible


def _entregado_hace(pedido, dias: int) -> None:
    """Deja el pedido entregado hace N días, sin pasar por el servicio.

    Es la única forma de probar la mora: el plazo se cuenta desde la entrega, y
    una prueba no puede esperar treinta días. Se toca también `fecha_pedido`
    porque la restricción `pedido_distribucion_fechas_coherentes` no deja
    entregar antes de pedir.
    """
    hace = timezone.now() - timedelta(days=dias)
    PedidoDistribucion.objects.filter(pk=pedido.pk).update(
        estado=PedidoDistribucion.Estado.ENTREGADO, fecha_pedido=hace, fecha_entrega=hace
    )


def _pedido_ajeno() -> PedidoDistribucion:
    """Un pedido entero de otro negocio: su tienda, su producto y quien lo tomó."""
    ajena = FabricaDeClienteDistribucion()
    return pedidos.crear_pedido(
        cliente_distribucion_id=ajena.id,
        lineas=[
            LineaDePedidoDTO(
                producto_id=FabricaDeProducto(negocio=ajena.negocio).id,
                cantidad=Decimal("1.00"),
            )
        ],
        usuario_id=FabricaDeAdministrador(negocio=ajena.negocio).id,
        negocio_id=ajena.negocio_id,
    )


# --------------------------------------------------------------------------- #
# Tomar el pedido
# --------------------------------------------------------------------------- #
def test_crear_pedido_congela_el_precio_mayorista(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    linea = pedido.detalles.get()
    assert linea.precio_unitario == Decimal("3500.00")
    assert total_de_un_pedido(pedido_id=pedido.id, negocio_id=negocio.id) == Decimal("35000.00")


def test_subir_el_precio_no_reescribe_un_pedido_ya_tomado(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    producto = bodega.producto
    producto.precio_mayorista = Decimal("9000.00")
    producto.save(update_fields=["precio_mayorista", "actualizado_en"])

    assert pedido.detalles.get().precio_unitario == Decimal("3500.00")


def test_crear_pedido_no_toca_el_inventario(negocio, tienda, bodega, administrador):
    """Un pedido pendiente todavía no salió de la bodega (decisión 4)."""
    _pedir(negocio, tienda, bodega, administrador)

    assert _disponible(bodega) == Decimal("100.00")
    assert not MovimientoInventario.objects.filter(referencia_tipo=REFERENCIA).exists()


def test_un_pedido_sin_lineas_no_es_un_pedido(negocio, tienda, administrador):
    with pytest.raises(PedidoSinLineas):
        pedidos.crear_pedido(
            cliente_distribucion_id=tienda.id,
            lineas=[],
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )


def test_no_se_pide_un_producto_de_otro_negocio(negocio, tienda, administrador):
    ajeno = FabricaDeProducto()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        pedidos.crear_pedido(
            cliente_distribucion_id=tienda.id,
            lineas=[LineaDePedidoDTO(producto_id=ajeno.id, cantidad=Decimal("1.00"))],
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )


def test_no_se_le_pide_a_una_tienda_de_otro_negocio(negocio, bodega, administrador):
    ajena = FabricaDeClienteDistribucion()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        pedidos.crear_pedido(
            cliente_distribucion_id=ajena.id,
            lineas=[LineaDePedidoDTO(producto_id=bodega.producto_id, cantidad=Decimal("1.00"))],
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )


# --------------------------------------------------------------------------- #
# Despachar
# --------------------------------------------------------------------------- #
def test_despachar_descuenta_de_la_bodega(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    despachado = _despachar(pedido, negocio, bodega, administrador)

    assert despachado.estado == PedidoDistribucion.Estado.EN_RUTA
    assert _disponible(bodega) == Decimal("90.00")


def test_el_despacho_deja_su_rastro_en_el_kardex(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    _despachar(pedido, negocio, bodega, administrador)

    movimiento = MovimientoInventario.objects.get(referencia_tipo=REFERENCIA)
    assert movimiento.cantidad == Decimal("-10.00")
    assert movimiento.referencia_id == pedido.id
    assert movimiento.usuario_id == administrador.id


def test_despachar_sin_existencias_falla_y_deja_el_pedido_donde_estaba(
    negocio, tienda, bodega, administrador
):
    """La transacción es de verdad: ni sale mercancía ni cambia el estado."""
    pedido = _pedir(negocio, tienda, bodega, administrador, cantidad="500.00")

    with pytest.raises(ExistenciasInsuficientes):
        _despachar(pedido, negocio, bodega, administrador)

    pedido.refresh_from_db()
    assert pedido.estado == PedidoDistribucion.Estado.PENDIENTE
    assert _disponible(bodega) == Decimal("100.00")


def test_un_pedido_en_ruta_no_se_despacha_otra_vez(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    with pytest.raises(PedidoNoDespachable):
        _despachar(pedido, negocio, bodega, administrador)

    assert _disponible(bodega) == Decimal("90.00")


# --------------------------------------------------------------------------- #
# Entregar, no entregar y volver a despachar
# --------------------------------------------------------------------------- #
def test_entregar_graba_la_fecha_de_entrega(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    entregado = pedidos.entregar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    assert entregado.estado == PedidoDistribucion.Estado.ENTREGADO
    assert entregado.esta_entregado


def test_no_se_entrega_lo_que_no_va_en_el_camion(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    with pytest.raises(PedidoNoEntregable):
        pedidos.entregar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)


def test_no_entregar_devuelve_el_stock_en_el_acto(negocio, tienda, bodega, administrador):
    """Decisión 5: la mercancía vuelve ya, no cuando llegue el camión."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    devuelto = pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="La tienda estaba cerrada.",
    )

    assert devuelto.estado == PedidoDistribucion.Estado.NO_ENTREGADO
    assert _disponible(bodega) == Decimal("100.00")


def test_no_entregar_sin_motivo_no_se_puede(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    with pytest.raises(MotivoObligatorio):
        pedidos.marcar_no_entregado(
            pedido_id=pedido.id,
            negocio_id=negocio.id,
            usuario_id=administrador.id,
            motivo="   ",
        )


def test_el_motivo_queda_en_la_nota_de_la_devolucion(negocio, tienda, bodega, administrador):
    """Es donde alguien lo va a buscar cuando pregunte por qué subió el saldo."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="Nadie recibió.",
    )

    devolucion = MovimientoInventario.objects.get(
        referencia_tipo=REFERENCIA, referencia_id=pedido.id, cantidad__gt=0
    )
    assert devolucion.nota == "Nadie recibió."


def test_un_pedido_no_entregado_se_vuelve_a_despachar_y_vuelve_a_descontar(
    negocio, tienda, bodega, administrador
):
    """El ciclo completo. Es lo que justifica leer el kardex y no las líneas:
    devolver por el pedido devolvería el doble en la segunda vuelta."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)
    pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="La tienda estaba cerrada.",
    )

    otra_vez = _despachar(pedido, negocio, bodega, administrador)

    assert otra_vez.estado == PedidoDistribucion.Estado.EN_RUTA
    assert otra_vez.motivo_no_entrega == ""
    assert _disponible(bodega) == Decimal("90.00")


def test_devolver_dos_veces_no_repone_de_mas(negocio, tienda, bodega, administrador):
    """El neto del kardex ya es cero: la segunda devolución no mueve nada."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)
    pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="Cerrada.",
    )
    _despachar(pedido, negocio, bodega, administrador)
    pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="Cerrada otra vez.",
    )

    assert _disponible(bodega) == Decimal("100.00")


# --------------------------------------------------------------------------- #
# Cancelar
# --------------------------------------------------------------------------- #
def test_cancelar_un_pedido_pendiente(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)

    cancelado = pedidos.cancelar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    assert cancelado.estado == PedidoDistribucion.Estado.CANCELADO
    assert _disponible(bodega) == Decimal("100.00")


def test_no_se_cancela_lo_que_va_en_el_camion(negocio, tienda, bodega, administrador):
    """Cancelar en ruta dejaría el saldo descontado sin nada que lo explique."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)

    with pytest.raises(PedidoNoCancelable):
        pedidos.cancelar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)


def test_un_pedido_ya_entregado_no_se_cancela(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)
    pedidos.entregar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    with pytest.raises(PedidoNoCancelable):
        pedidos.cancelar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)


def test_un_pedido_no_entregado_si_se_cancela(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _despachar(pedido, negocio, bodega, administrador)
    pedidos.marcar_no_entregado(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="La tienda cerró para siempre.",
    )

    cancelado = pedidos.cancelar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    assert cancelado.estado == PedidoDistribucion.Estado.CANCELADO
    assert _disponible(bodega) == Decimal("100.00")


# --------------------------------------------------------------------------- #
# Abonos
# --------------------------------------------------------------------------- #
def test_los_abonos_van_bajando_el_saldo(negocio, tienda, bodega, administrador):
    """Aquí sí hay abonos, al revés que en el bar."""
    pedido = _pedir(negocio, tienda, bodega, administrador)

    primero = pagos.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("20000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )
    segundo = pagos.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("15000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )

    assert primero.saldo == Decimal("15000.00")
    assert segundo.saldo == Decimal("0.00")
    assert saldo_de_un_pedido(pedido_id=pedido.id, negocio_id=negocio.id).pagado == Decimal(
        "35000.00"
    )


def test_un_abono_que_pasa_del_total_se_rechaza(negocio, tienda, bodega, administrador):
    """La suma de los pagos es un agregado: no la puede frenar la base."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    pagos.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("30000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )

    with pytest.raises(PagoSuperaElTotal):
        pagos.registrar_pago(
            pedido_id=pedido.id,
            negocio_id=negocio.id,
            monto=Decimal("6000.00"),
            metodo=METODO,
            recibido_por_id=administrador.id,
        )

    assert PagoDistribucion.objects.filter(pedido_distribucion=pedido).count() == 1


def test_un_pedido_cancelado_no_admite_abonos(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    pedidos.cancelar_pedido(pedido_id=pedido.id, negocio_id=negocio.id)

    with pytest.raises(PedidoNoCobrable):
        pagos.registrar_pago(
            pedido_id=pedido.id,
            negocio_id=negocio.id,
            monto=Decimal("1000.00"),
            metodo=METODO,
            recibido_por_id=administrador.id,
        )


def test_el_saldo_de_una_tienda_no_cuenta_lo_cancelado(negocio, tienda, bodega, administrador):
    _pedir(negocio, tienda, bodega, administrador)
    cancelado = _pedir(negocio, tienda, bodega, administrador)
    pedidos.cancelar_pedido(pedido_id=cancelado.id, negocio_id=negocio.id)

    assert saldo_de_un_cliente(cliente_id=tienda.id, negocio_id=negocio.id) == Decimal("35000.00")


# --------------------------------------------------------------------------- #
# Mora
# --------------------------------------------------------------------------- #
def test_una_tienda_con_el_plazo_vencido_sale_en_mora(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _entregado_hace(pedido, dias=40)

    morosos = list(clientes_en_mora(negocio_id=negocio.id))

    assert [cliente.id for cliente in morosos] == [tienda.id]
    assert morosos[0].deuda_vencida == Decimal("35000.00")


def test_una_tienda_dentro_del_plazo_no_esta_en_mora(negocio, tienda, bodega, administrador):
    """Un pedido de hace diez días a treinta días no es mora, es crédito."""
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _entregado_hace(pedido, dias=10)

    assert not clientes_en_mora(negocio_id=negocio.id).exists()


def test_un_pedido_sin_entregar_no_vence(negocio, tienda, bodega, administrador):
    """El plazo corre desde que la tienda recibe, no desde que pide."""
    _pedir(negocio, tienda, bodega, administrador)

    assert not clientes_en_mora(negocio_id=negocio.id).exists()


def test_la_mora_descuenta_lo_ya_abonado(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _entregado_hace(pedido, dias=40)
    pagos.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("30000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )

    assert clientes_en_mora(negocio_id=negocio.id).get().deuda_vencida == Decimal("5000.00")


def test_una_tienda_que_ya_pago_sale_de_la_mora(negocio, tienda, bodega, administrador):
    pedido = _pedir(negocio, tienda, bodega, administrador)
    _entregado_hace(pedido, dias=40)
    pagos.registrar_pago(
        pedido_id=pedido.id,
        negocio_id=negocio.id,
        monto=Decimal("35000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )

    assert not clientes_en_mora(negocio_id=negocio.id).exists()


def test_la_mora_de_dos_pedidos_se_suma_una_sola_vez(negocio, tienda, bodega, administrador):
    """Con dos `Sum` en la misma consulta cada total saldría inflado por el otro."""
    primero = _pedir(negocio, tienda, bodega, administrador)
    segundo = _pedir(negocio, tienda, bodega, administrador)
    _entregado_hace(primero, dias=40)
    _entregado_hace(segundo, dias=50)
    pagos.registrar_pago(
        pedido_id=primero.id,
        negocio_id=negocio.id,
        monto=Decimal("5000.00"),
        metodo=METODO,
        recibido_por_id=administrador.id,
    )

    assert clientes_en_mora(negocio_id=negocio.id).get().deuda_vencida == Decimal("65000.00")


def test_la_mora_de_otro_negocio_no_se_ve(negocio):
    pedido = _pedido_ajeno()
    _entregado_hace(pedido, dias=40)

    assert not clientes_en_mora(negocio_id=negocio.id).exists()


# --------------------------------------------------------------------------- #
# Tiendas cliente y aislamiento
# --------------------------------------------------------------------------- #
def test_no_hay_dos_tiendas_con_el_mismo_nit(negocio):
    datos = DatosDeClienteDistribucionDTO(razon_social="Tienda La Esquina", nit="900123456")
    servicio_de_clientes.registrar_cliente(negocio_id=negocio.id, datos=datos)

    with pytest.raises(NitDuplicado):
        servicio_de_clientes.registrar_cliente(negocio_id=negocio.id, datos=datos)


def test_dos_negocios_si_pueden_tener_el_mismo_nit(negocio):
    """La unicidad es por negocio: dos bares pueden venderle a la misma tienda."""
    datos = DatosDeClienteDistribucionDTO(razon_social="Tienda La Esquina", nit="900123456")
    otro = FabricaDeClienteDistribucion().negocio

    servicio_de_clientes.registrar_cliente(negocio_id=negocio.id, datos=datos)
    creado = servicio_de_clientes.registrar_cliente(negocio_id=otro.id, datos=datos)

    assert creado.pk is not None


def test_desactivar_una_tienda_no_la_borra(negocio, tienda):
    desactivada = servicio_de_clientes.desactivar_cliente(
        cliente_id=tienda.id, negocio_id=negocio.id
    )

    assert desactivada.activo is False


def test_no_se_toca_el_pedido_de_otro_negocio(negocio):
    pedido = _pedido_ajeno()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        obtener_pedido(pedido_id=pedido.id, negocio_id=negocio.id)


def test_no_se_despacha_el_pedido_de_otro_negocio(negocio, bodega, administrador):
    pedido = _pedido_ajeno()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        _despachar(pedido, negocio, bodega, administrador)

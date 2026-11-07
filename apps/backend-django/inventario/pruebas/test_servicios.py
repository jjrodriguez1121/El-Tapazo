"""Pruebas del inventario.

Es el corazón del sistema: si las existencias quedan mal, el sistema no sirve.
Lo que se comprueba una y otra vez es la **invariante del módulo**: el saldo
cacheado es siempre la suma del kardex.
"""

from decimal import Decimal

import pytest

from catalogo.pruebas.fabricas import FabricaDeProducto
from inventario.dtos import LineaDeProductoDTO
from inventario.excepciones import (
    CantidadInvalida,
    ExistenciasInsuficientes,
    MotivoObligatorio,
    MovimientoYaAnulado,
)
from inventario.models import Existencia, MovimientoInventario
from inventario.pruebas.fabricas import FabricaDeExistencia, FabricaDeUbicacion
from inventario.repositorios import movimientos as repositorio
from inventario.servicios import ajustes, consumo, operaciones
from nucleo.excepciones import NoEncontradoEnEsteNegocio

pytestmark = pytest.mark.django_db

Referencia = MovimientoInventario.ReferenciaTipo


def _saldo(existencia: Existencia) -> Decimal:
    existencia.refresh_from_db()
    return existencia.cantidad_disponible


def _saldo_segun_kardex(existencia: Existencia) -> Decimal:
    return repositorio.saldo_segun_kardex(
        producto_id=existencia.producto_id,
        ubicacion_id=existencia.ubicacion_id,
        negocio_id=existencia.negocio_id,
    )


# --------------------------------------------------------------------------- #
# Entradas y salidas
# --------------------------------------------------------------------------- #
def test_una_entrada_crea_la_existencia_si_no_habia(negocio, administrador):
    """El movimiento positivo sí crea la fila: la mercancía llegó de verdad."""
    producto = FabricaDeProducto(negocio=negocio)
    bodega = FabricaDeUbicacion(negocio=negocio)

    operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=bodega.id,
        lineas=[LineaDeProductoDTO(producto_id=producto.id, cantidad=Decimal("24.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    existencia = Existencia.objects.get(producto=producto, ubicacion=bodega)
    assert existencia.cantidad_disponible == Decimal("24.00")


def test_vender_descuenta_el_stock_y_deja_el_movimiento_en_negativo(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("3.00"))],
        ubicacion_id=existencia.ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_EVENTO,
        referencia_id=42,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    assert _saldo(existencia) == Decimal("7.00")
    movimiento = MovimientoInventario.objects.get()
    assert movimiento.cantidad == Decimal("-3.00")
    assert movimiento.referencia_id == 42


def test_vender_sin_stock_falla_y_no_deja_ni_el_movimiento(negocio, administrador):
    """Verifica que la transacción es de verdad: media venta es peor que ninguna."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("2.00"))

    with pytest.raises(ExistenciasInsuficientes):
        consumo.descontar_por_venta(
            lineas=[
                LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("5.00"))
            ],
            ubicacion_id=existencia.ubicacion_id,
            referencia_tipo=Referencia.PEDIDO_EVENTO,
            referencia_id=1,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    assert _saldo(existencia) == Decimal("2.00")
    assert MovimientoInventario.objects.count() == 0


def test_si_una_linea_de_la_venta_no_alcanza_no_sale_ninguna(negocio, administrador):
    hay = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    falta = FabricaDeExistencia(
        negocio=negocio, ubicacion=hay.ubicacion, cantidad_disponible=Decimal("1.00")
    )

    with pytest.raises(ExistenciasInsuficientes):
        consumo.descontar_por_venta(
            lineas=[
                LineaDeProductoDTO(producto_id=hay.producto_id, cantidad=Decimal("2.00")),
                LineaDeProductoDTO(producto_id=falta.producto_id, cantidad=Decimal("9.00")),
            ],
            ubicacion_id=hay.ubicacion_id,
            referencia_tipo=Referencia.PEDIDO_EVENTO,
            referencia_id=1,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    assert _saldo(hay) == Decimal("10.00")
    assert _saldo(falta) == Decimal("1.00")


def test_vender_algo_que_nunca_ha_existido_no_crea_una_fila_en_cero(negocio, administrador):
    """Crear filas en cero cada vez que alguien pide lo que no hay llenaría la
    tabla de basura."""
    producto = FabricaDeProducto(negocio=negocio)
    bodega = FabricaDeUbicacion(negocio=negocio)

    with pytest.raises(ExistenciasInsuficientes) as error:
        consumo.descontar_por_venta(
            lineas=[LineaDeProductoDTO(producto_id=producto.id, cantidad=Decimal("1.00"))],
            ubicacion_id=bodega.id,
            referencia_tipo=Referencia.PEDIDO_EVENTO,
            referencia_id=1,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    assert error.value.detalles["disponible"] == "0.00"
    assert Existencia.objects.count() == 0


def test_las_lineas_repetidas_del_mismo_producto_se_suman(negocio, administrador):
    """«2 Águila» y «3 Águila» son cinco unidades que salen, no dos operaciones
    sobre la misma fila con el saldo leído a destiempo."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    consumo.descontar_por_venta(
        lineas=[
            LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("2.00")),
            LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("3.00")),
        ],
        ubicacion_id=existencia.ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_EVENTO,
        referencia_id=1,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    assert _saldo(existencia) == Decimal("5.00")
    assert MovimientoInventario.objects.count() == 1


def test_no_se_puede_mover_el_inventario_de_otro_negocio(negocio, administrador):
    ajena = FabricaDeExistencia()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        consumo.descontar_por_venta(
            lineas=[LineaDeProductoDTO(producto_id=ajena.producto_id, cantidad=Decimal("1.00"))],
            ubicacion_id=ajena.ubicacion_id,
            referencia_tipo=Referencia.PEDIDO_EVENTO,
            referencia_id=1,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )


def test_una_merma_sin_motivo_no_pasa(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    with pytest.raises(MotivoObligatorio):
        operaciones.registrar_merma(
            ubicacion_id=existencia.ubicacion_id,
            lineas=[
                LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("1.00"))
            ],
            usuario_id=administrador.id,
            negocio_id=negocio.id,
            motivo="   ",
        )


def test_la_merma_tiene_tipo_propio_y_no_es_una_salida_con_nota(negocio, administrador):
    """Con un `tipo` el informe de mermas sale sin leer textos libres."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    operaciones.registrar_merma(
        ubicacion_id=existencia.ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("2.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
        motivo="Se cayó una caja.",
    )

    movimiento = MovimientoInventario.objects.get()
    assert movimiento.tipo == MovimientoInventario.Tipo.MERMA
    assert _saldo(existencia) == Decimal("8.00")


# --------------------------------------------------------------------------- #
# Traslados
# --------------------------------------------------------------------------- #
def test_un_traslado_deja_dos_filas_y_no_cambia_el_total_del_negocio(negocio, administrador):
    """La invariante del traslado, y la decisión más fácil de romper."""
    origen = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    destino = FabricaDeUbicacion(negocio=negocio)

    movimientos = operaciones.transferir_entre_ubicaciones(
        producto_id=origen.producto_id,
        origen_id=origen.ubicacion_id,
        destino_id=destino.id,
        cantidad=Decimal("4.00"),
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    en_destino = Existencia.objects.get(producto=origen.producto, ubicacion=destino)
    assert len(movimientos) == 2
    assert _saldo(origen) == Decimal("6.00")
    assert en_destino.cantidad_disponible == Decimal("4.00")
    assert _saldo(origen) + en_destino.cantidad_disponible == Decimal("10.00")


def test_las_dos_filas_del_traslado_comparten_referencia(negocio, administrador):
    origen = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    destino = FabricaDeUbicacion(negocio=negocio)

    movimientos = operaciones.transferir_entre_ubicaciones(
        producto_id=origen.producto_id,
        origen_id=origen.ubicacion_id,
        destino_id=destino.id,
        cantidad=Decimal("4.00"),
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    referencias = {movimiento.referencia_id for movimiento in movimientos}
    assert len(referencias) == 1
    assert referencias != {None}


def test_no_se_traslada_a_la_misma_ubicacion(negocio, administrador):
    origen = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    with pytest.raises(CantidadInvalida):
        operaciones.transferir_entre_ubicaciones(
            producto_id=origen.producto_id,
            origen_id=origen.ubicacion_id,
            destino_id=origen.ubicacion_id,
            cantidad=Decimal("1.00"),
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )


# --------------------------------------------------------------------------- #
# Anulaciones
# --------------------------------------------------------------------------- #
def test_anular_crea_el_movimiento_contrario_y_no_borra_nada(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    entrada = operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=existencia.ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("6.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )[0]

    contrario = operaciones.anular_movimiento(
        movimiento_id=entrada.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="Se contó mal la remesa.",
    )

    assert contrario.cantidad == Decimal("-6.00")
    assert MovimientoInventario.objects.count() == 2
    assert _saldo(existencia) == Decimal("0.00")


def test_no_se_anula_dos_veces_el_mismo_movimiento(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    entrada = operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=existencia.ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("6.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )[0]
    operaciones.anular_movimiento(
        movimiento_id=entrada.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        motivo="Se contó mal.",
    )

    with pytest.raises(MovimientoYaAnulado):
        operaciones.anular_movimiento(
            movimiento_id=entrada.id,
            negocio_id=negocio.id,
            usuario_id=administrador.id,
            motivo="Otra vez.",
        )


def test_anular_una_entrada_ya_vendida_falla_por_existencias(negocio, administrador):
    """El caso feo, el que nadie prueba: si lo que entró de más ya se vendió,
    deshacer la entrada dejaría el saldo en negativo."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    entrada = operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=existencia.ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("6.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )[0]
    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("5.00"))],
        ubicacion_id=existencia.ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_EVENTO,
        referencia_id=1,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    with pytest.raises(ExistenciasInsuficientes):
        operaciones.anular_movimiento(
            movimiento_id=entrada.id,
            negocio_id=negocio.id,
            usuario_id=administrador.id,
            motivo="Llegó de menos.",
        )

    assert _saldo(existencia) == Decimal("1.00")


# --------------------------------------------------------------------------- #
# Ajuste contra reconstrucción
# --------------------------------------------------------------------------- #
def test_el_ajuste_recibe_lo_contado_y_calcula_la_diferencia(negocio, administrador):
    """Quien cuenta cuenta cajas, no calcula restas."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    movimiento = ajustes.ajustar_existencias(
        producto_id=existencia.producto_id,
        ubicacion_id=existencia.ubicacion_id,
        negocio_id=negocio.id,
        cantidad_contada=Decimal("7.00"),
        usuario_id=administrador.id,
        motivo="Conteo del lunes.",
    )

    assert movimiento.cantidad == Decimal("-3.00")
    assert movimiento.tipo == MovimientoInventario.Tipo.AJUSTE
    assert _saldo(existencia) == Decimal("7.00")


def test_si_el_conteo_coincide_no_hay_movimiento(negocio, administrador):
    """Un movimiento de cero no es un movimiento, y la base lo prohíbe."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    movimiento = ajustes.ajustar_existencias(
        producto_id=existencia.producto_id,
        ubicacion_id=existencia.ubicacion_id,
        negocio_id=negocio.id,
        cantidad_contada=Decimal("10.00"),
        usuario_id=administrador.id,
        motivo="Conteo del lunes.",
    )

    assert movimiento is None
    assert MovimientoInventario.objects.count() == 0


def test_un_ajuste_sin_motivo_no_pasa(negocio, administrador):
    """Es la tabla donde se detecta un faltante: sin autor y sin motivo no sirve."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    with pytest.raises(MotivoObligatorio):
        ajustes.ajustar_existencias(
            producto_id=existencia.producto_id,
            ubicacion_id=existencia.ubicacion_id,
            negocio_id=negocio.id,
            cantidad_contada=Decimal("7.00"),
            usuario_id=administrador.id,
            motivo="",
        )


def test_reconstruir_el_saldo_no_inventa_un_movimiento(negocio, administrador):
    """Inventar un ajuste falsearía la historia de la mercancía."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=existencia.ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("6.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )
    # El caché se desvía a mano, simulando el bug que esto repara.
    Existencia.objects.filter(pk=existencia.pk).update(cantidad_disponible=Decimal("99.00"))

    reparada = ajustes.reconstruir_saldo_desde_kardex(
        producto_id=existencia.producto_id,
        ubicacion_id=existencia.ubicacion_id,
        negocio_id=negocio.id,
    )

    assert reparada.cantidad_disponible == Decimal("6.00")
    assert MovimientoInventario.objects.count() == 1


# --------------------------------------------------------------------------- #
# Devolver lo que movió una referencia
# --------------------------------------------------------------------------- #
def test_devolver_lo_movido_repone_exactamente_lo_que_salio(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("4.00"))],
        ubicacion_id=existencia.ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
        referencia_id=7,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    consumo.devolver_lo_movido_por(
        referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
        referencia_id=7,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    assert _saldo(existencia) == Decimal("10.00")


def test_el_ciclo_despacho_no_entrega_despacho_no_devuelve_el_doble(negocio, administrador):
    """Es lo que justifica leer el kardex y no las líneas del pedido: el kardex
    acumula −X, +X, −X y solo el neto sabe cuánto está fuera de verdad."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    linea = [LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("4.00"))]

    def despachar():
        consumo.descontar_por_venta(
            lineas=linea,
            ubicacion_id=existencia.ubicacion_id,
            referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
            referencia_id=7,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    def devolver():
        return consumo.devolver_lo_movido_por(
            referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
            referencia_id=7,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    despachar()
    devolver()
    despachar()

    assert _saldo(existencia) == Decimal("6.00")
    devolver()
    assert _saldo(existencia) == Decimal("10.00")


def test_devolver_dos_veces_seguidas_no_repone_de_mas(negocio, administrador):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("4.00"))],
        ubicacion_id=existencia.ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
        referencia_id=7,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    consumo.devolver_lo_movido_por(
        referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
        referencia_id=7,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )
    segunda = consumo.devolver_lo_movido_por(
        referencia_tipo=Referencia.PEDIDO_DISTRIBUCION,
        referencia_id=7,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    assert segunda == []
    assert _saldo(existencia) == Decimal("10.00")


# --------------------------------------------------------------------------- #
# La invariante del módulo
# --------------------------------------------------------------------------- #
def test_el_saldo_cacheado_es_siempre_la_suma_del_kardex(negocio, administrador):
    """Seis operaciones mezcladas. Si esto falla, el módulo entero está mal."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    otra_bodega = FabricaDeUbicacion(negocio=negocio)
    producto_id = existencia.producto_id
    ubicacion_id = existencia.ubicacion_id

    operaciones.registrar_entrada_de_mercancia(
        ubicacion_id=ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=producto_id, cantidad=Decimal("20.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )
    consumo.descontar_por_venta(
        lineas=[LineaDeProductoDTO(producto_id=producto_id, cantidad=Decimal("5.00"))],
        ubicacion_id=ubicacion_id,
        referencia_tipo=Referencia.PEDIDO_EVENTO,
        referencia_id=1,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )
    operaciones.registrar_merma(
        ubicacion_id=ubicacion_id,
        lineas=[LineaDeProductoDTO(producto_id=producto_id, cantidad=Decimal("2.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
        motivo="Se rompieron.",
    )
    operaciones.transferir_entre_ubicaciones(
        producto_id=producto_id,
        origen_id=ubicacion_id,
        destino_id=otra_bodega.id,
        cantidad=Decimal("3.00"),
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )
    ajustes.ajustar_existencias(
        producto_id=producto_id,
        ubicacion_id=ubicacion_id,
        negocio_id=negocio.id,
        cantidad_contada=Decimal("9.00"),
        usuario_id=administrador.id,
        motivo="Conteo.",
    )
    consumo.devolver_lo_movido_por(
        referencia_tipo=Referencia.PEDIDO_EVENTO,
        referencia_id=1,
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    en_destino = Existencia.objects.get(producto_id=producto_id, ubicacion=otra_bodega)
    assert _saldo(existencia) == _saldo_segun_kardex(existencia)
    assert en_destino.cantidad_disponible == _saldo_segun_kardex(en_destino)

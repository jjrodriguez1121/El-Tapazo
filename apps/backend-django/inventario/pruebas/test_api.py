"""Pruebas de los endpoints del inventario.

Lo propio de esta app es el reparto de permisos: mover mercancía es de
administrador, pero el equipo entero **lee** las existencias. Un mesero tiene
que poder mirar si queda cerveza sin poder tocar el kardex.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from inventario.models import Existencia, MovimientoInventario
from inventario.pruebas.fabricas import FabricaDeExistencia, FabricaDeUbicacion

pytestmark = pytest.mark.django_db

URL_EXISTENCIAS = reverse("inventario:existencia-list")
URL_UBICACIONES = reverse("inventario:ubicacion-list")
URL_MOVIMIENTOS = reverse("inventario:movimiento-list")
URL_ENTRADAS = reverse("inventario:movimiento-entradas")
URL_TRASLADOS = reverse("inventario:movimiento-traslados")
URL_AJUSTES = reverse("inventario:movimiento-ajustes")
URL_MERMAS = reverse("inventario:movimiento-mermas")
URL_BAJO_MINIMO = reverse("inventario:existencia-bajo-minimo")
URL_MINIMO = reverse("inventario:existencia-minimo")
URL_VALORIZACION = reverse("inventario:valorizacion")


# --------------------------------------------------------------------------- #
# Permisos
# --------------------------------------------------------------------------- #
def test_sin_iniciar_sesion_no_se_ve_nada(cliente_api):
    respuesta = cliente_api.get(URL_EXISTENCIAS)

    assert respuesta.status_code == 401


def test_un_mesero_si_puede_mirar_si_queda_cerveza(cliente_api_autenticado, mesero, negocio):
    FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    respuesta = cliente_api_autenticado(mesero).get(URL_EXISTENCIAS)

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1


def test_un_mesero_no_puede_mover_el_inventario(cliente_api_autenticado, mesero, negocio):
    """Las existencias no se mueven a mano al vender: se mueven solas."""
    bodega = FabricaDeUbicacion(negocio=negocio)

    respuesta = cliente_api_autenticado(mesero).post(
        URL_ENTRADAS,
        {"ubicacion_id": bodega.id, "lineas": [{"producto_id": 1, "cantidad": "5.00"}]},
        format="json",
    )

    assert respuesta.status_code == 403
    assert MovimientoInventario.objects.count() == 0


def test_un_mesero_no_ve_el_kardex(cliente_api_autenticado, mesero):
    """El kardex dice dónde se perdieron doce cervezas: no es conversación de barra."""
    respuesta = cliente_api_autenticado(mesero).get(URL_MOVIMIENTOS)

    assert respuesta.status_code == 403


def test_un_cajero_tampoco_mueve_el_inventario(cliente_api_autenticado, cajero, negocio):
    bodega = FabricaDeUbicacion(negocio=negocio)

    respuesta = cliente_api_autenticado(cajero).post(
        URL_ENTRADAS,
        {"ubicacion_id": bodega.id, "lineas": [{"producto_id": 1, "cantidad": "5.00"}]},
        format="json",
    )

    assert respuesta.status_code == 403


# --------------------------------------------------------------------------- #
# Aislamiento entre negocios
# --------------------------------------------------------------------------- #
def test_solo_se_ven_las_existencias_del_negocio(cliente_api_autenticado, mesero, negocio):
    FabricaDeExistencia(negocio=negocio)
    FabricaDeExistencia()  # de otro negocio

    respuesta = cliente_api_autenticado(mesero).get(URL_EXISTENCIAS)

    assert respuesta.data["count"] == 1


def test_no_se_mueve_el_inventario_de_otro_negocio(cliente_api_autenticado, administrador):
    ajena = FabricaDeExistencia(cantidad_disponible=Decimal("50.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        URL_ENTRADAS,
        {
            "ubicacion_id": ajena.ubicacion_id,
            "lineas": [{"producto_id": ajena.producto_id, "cantidad": "5.00"}],
        },
        format="json",
    )

    assert respuesta.status_code == 404
    ajena.refresh_from_db()
    assert ajena.cantidad_disponible == Decimal("50.00")


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #
def test_registrar_una_entrada_devuelve_201_y_sube_el_saldo(
    cliente_api_autenticado, administrador, negocio
):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        URL_ENTRADAS,
        {
            "ubicacion_id": existencia.ubicacion_id,
            "lineas": [{"producto_id": existencia.producto_id, "cantidad": "24.00"}],
            "nota": "Remesa del lunes",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data[0]["cantidad"] == "24.00"
    existencia.refresh_from_db()
    assert existencia.cantidad_disponible == Decimal("24.00")


def test_un_traslado_devuelve_las_dos_filas(cliente_api_autenticado, administrador, negocio):
    origen = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    destino = FabricaDeUbicacion(negocio=negocio)

    respuesta = cliente_api_autenticado(administrador).post(
        URL_TRASLADOS,
        {
            "producto_id": origen.producto_id,
            "origen_id": origen.ubicacion_id,
            "destino_id": destino.id,
            "cantidad": "4.00",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert len(respuesta.data) == 2
    assert {fila["cantidad"] for fila in respuesta.data} == {"-4.00", "4.00"}


def test_sacar_mas_de_lo_que_hay_devuelve_409_con_el_detalle(
    cliente_api_autenticado, administrador, negocio
):
    """El `detalles` es lo que deja a la pantalla decir «quedan 2»."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("2.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        URL_MERMAS,
        {
            "ubicacion_id": existencia.ubicacion_id,
            "lineas": [{"producto_id": existencia.producto_id, "cantidad": "5.00"}],
            "motivo": "Se rompieron.",
        },
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "existencias_insuficientes"
    assert respuesta.data["error"]["detalles"]["disponible"] == "2.00"


def test_una_merma_sin_motivo_devuelve_400(cliente_api_autenticado, administrador, negocio):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        URL_MERMAS,
        {
            "ubicacion_id": existencia.ubicacion_id,
            "lineas": [{"producto_id": existencia.producto_id, "cantidad": "1.00"}],
            "motivo": "",
        },
        format="json",
    )

    assert respuesta.status_code == 400


def test_un_ajuste_que_coincide_devuelve_204(cliente_api_autenticado, administrador, negocio):
    """Un movimiento de cero no es un movimiento."""
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        URL_AJUSTES,
        {
            "producto_id": existencia.producto_id,
            "ubicacion_id": existencia.ubicacion_id,
            "cantidad_contada": "10.00",
            "motivo": "Conteo del lunes.",
        },
        format="json",
    )

    assert respuesta.status_code == 204
    assert MovimientoInventario.objects.count() == 0


def test_anular_un_movimiento_devuelve_el_contrario(
    cliente_api_autenticado, administrador, negocio
):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    cliente = cliente_api_autenticado(administrador)
    entrada = cliente.post(
        URL_ENTRADAS,
        {
            "ubicacion_id": existencia.ubicacion_id,
            "lineas": [{"producto_id": existencia.producto_id, "cantidad": "6.00"}],
        },
        format="json",
    ).data[0]

    respuesta = cliente.post(
        reverse("inventario:movimiento-anulacion", args=[entrada["id"]]),
        {"motivo": "Se contó mal la remesa."},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["cantidad"] == "-6.00"
    assert MovimientoInventario.objects.count() == 2


# --------------------------------------------------------------------------- #
# Reposición y valorización
# --------------------------------------------------------------------------- #
def test_bajo_minimo_solo_trae_lo_que_tiene_minimo_puesto(cliente_api_autenticado, mesero, negocio):
    """Un cero es «sin alerta», no «alerta siempre»."""
    FabricaDeExistencia(
        negocio=negocio, cantidad_disponible=Decimal("0.00"), cantidad_minima=Decimal("0.00")
    )
    escasa = FabricaDeExistencia(
        negocio=negocio, cantidad_disponible=Decimal("3.00"), cantidad_minima=Decimal("20.00")
    )

    respuesta = cliente_api_autenticado(mesero).get(URL_BAJO_MINIMO)

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["id"] == escasa.id


def test_fijar_el_minimo_es_de_administrador(cliente_api_autenticado, mesero, negocio):
    existencia = FabricaDeExistencia(negocio=negocio)

    respuesta = cliente_api_autenticado(mesero).post(
        URL_MINIMO,
        {
            "producto_id": existencia.producto_id,
            "ubicacion_id": existencia.ubicacion_id,
            "cantidad_minima": "20.00",
        },
        format="json",
    )

    assert respuesta.status_code == 403


def test_un_administrador_fija_el_minimo(cliente_api_autenticado, administrador, negocio):
    existencia = FabricaDeExistencia(
        negocio=negocio, cantidad_disponible=Decimal("3.00"), cantidad_minima=Decimal("0.00")
    )

    respuesta = cliente_api_autenticado(administrador).post(
        URL_MINIMO,
        {
            "producto_id": existencia.producto_id,
            "ubicacion_id": existencia.ubicacion_id,
            "cantidad_minima": "20.00",
        },
        format="json",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["esta_bajo_minimo"] is True


def test_la_valorizacion_multiplica_saldo_por_costo(
    cliente_api_autenticado, administrador, negocio
):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    existencia.producto.costo = Decimal("2000.00")
    existencia.producto.save(update_fields=["costo"])

    respuesta = cliente_api_autenticado(administrador).get(URL_VALORIZACION)

    assert respuesta.status_code == 200
    assert Decimal(respuesta.data["total"]) == Decimal("20000.00")


def test_crear_una_ubicacion_es_de_administrador(cliente_api_autenticado, administrador):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_UBICACIONES, {"nombre": "Bodega central", "tipo": "bodega"}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["nombre"] == "Bodega central"


def test_las_existencias_se_filtran_por_ubicacion(cliente_api_autenticado, mesero, negocio):
    barra = FabricaDeExistencia(negocio=negocio)
    FabricaDeExistencia(negocio=negocio)

    respuesta = cliente_api_autenticado(mesero).get(
        URL_EXISTENCIAS, {"ubicacion": barra.ubicacion_id}
    )

    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["ubicacion"]["id"] == barra.ubicacion_id


def test_el_kardex_se_filtra_por_producto(cliente_api_autenticado, administrador, negocio):
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("0.00"))
    cliente = cliente_api_autenticado(administrador)
    cliente.post(
        URL_ENTRADAS,
        {
            "ubicacion_id": existencia.ubicacion_id,
            "lineas": [{"producto_id": existencia.producto_id, "cantidad": "5.00"}],
        },
        format="json",
    )

    respuesta = cliente.get(URL_MOVIMIENTOS, {"producto": existencia.producto_id})

    assert respuesta.data["count"] == 1
    assert Existencia.objects.get(pk=existencia.pk).cantidad_disponible == Decimal("5.00")

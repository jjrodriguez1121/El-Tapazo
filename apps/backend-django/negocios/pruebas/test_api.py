"""Pruebas de los endpoints de negocios.

Lo propio de esta app es que hay **dos públicos**: el staff de la plataforma,
que administra negocios y no pertenece a ninguno, y la gente de un negocio, que
solo ve el suyo. Ninguno de los dos puede hacer lo del otro.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from distribucion.dtos import LineaDePedidoDTO
from distribucion.pruebas.fabricas import FabricaDeClienteDistribucion
from distribucion.servicios import pedidos as pedidos_de_mayoreo
from inventario.pruebas.fabricas import FabricaDeExistencia
from negocios.models import Negocio
from negocios.pruebas.fabricas import FabricaDeNegocio

pytestmark = pytest.mark.django_db

URL_NEGOCIOS = reverse("negocios:negocio-list")
URL_MI_NEGOCIO = reverse("negocios:mi-negocio")
URL_RESUMEN = reverse("negocios:resumen-de-ventas")

DATOS_DE_NEGOCIO = {"nombre_comercial": "Bar El Tapaso", "nit": "900999888"}


def _url(nombre: str, negocio_id: int) -> str:
    return reverse(f"negocios:negocio-{nombre}", args=[negocio_id])


# --------------------------------------------------------------------------- #
# La administración es del staff de la plataforma
# --------------------------------------------------------------------------- #
def test_sin_autenticar_no_se_ven_los_negocios(cliente_api):
    assert cliente_api.get(URL_NEGOCIOS).status_code == 401


def test_el_administrador_de_un_negocio_no_administra_la_plataforma(
    cliente_api_autenticado, administrador
):
    """Ni siquiera el suyo: dar de alta negocios es del staff."""
    respuesta = cliente_api_autenticado(administrador).get(URL_NEGOCIOS)

    assert respuesta.status_code == 403


def test_el_staff_lista_todos_los_negocios(cliente_api_autenticado, staff, negocio):
    FabricaDeNegocio()

    respuesta = cliente_api_autenticado(staff).get(URL_NEGOCIOS)

    assert respuesta.status_code == 200
    assert len(respuesta.data["results"]) == 2


def test_el_staff_da_de_alta_un_negocio(cliente_api_autenticado, staff):
    respuesta = cliente_api_autenticado(staff).post(URL_NEGOCIOS, DATOS_DE_NEGOCIO, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["estado"] == Negocio.Estado.ACTIVO


def test_repetir_el_nit_devuelve_409(cliente_api_autenticado, staff):
    cliente = cliente_api_autenticado(staff)
    cliente.post(URL_NEGOCIOS, DATOS_DE_NEGOCIO, format="json")

    respuesta = cliente.post(URL_NEGOCIOS, DATOS_DE_NEGOCIO, format="json")

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "nit_de_negocio_duplicado"


def test_un_negocio_que_no_existe_devuelve_404(cliente_api_autenticado, staff):
    respuesta = cliente_api_autenticado(staff).get(
        reverse("negocios:negocio-detail", args=[999999])
    )

    assert respuesta.status_code == 404


def test_suspender_y_reactivar_desde_la_api(cliente_api_autenticado, staff, negocio):
    cliente = cliente_api_autenticado(staff)

    suspension = cliente.post(_url("suspension", negocio.id))
    repetida = cliente.post(_url("suspension", negocio.id))
    reactivacion = cliente.post(_url("reactivacion", negocio.id))

    assert suspension.data["estado"] == Negocio.Estado.SUSPENDIDO
    assert repetida.status_code == 409
    assert repetida.data["error"]["codigo"] == "negocio_ya_suspendido"
    assert reactivacion.data["esta_operativo"] is True


def test_un_negocio_suspendido_no_deja_entrar_a_su_gente(
    cliente_api_autenticado, cliente_api, staff, negocio, administrador
):
    """Es lo que hace que suspender signifique algo: el inicio de sesión lo mira."""
    cliente_api_autenticado(staff).post(_url("suspension", negocio.id))
    cliente_api.force_authenticate(user=None)

    respuesta = cliente_api.post(
        reverse("usuarios:inicio-de-sesion"),
        {"correo": administrador.correo, "contrasena": "Tapaso.2026.segura"},
        format="json",
    )

    assert respuesta.status_code == 403
    assert respuesta.data["error"]["codigo"] == "negocio_suspendido"


# --------------------------------------------------------------------------- #
# Mi negocio
# --------------------------------------------------------------------------- #
def test_cualquiera_del_equipo_ve_su_negocio(cliente_api_autenticado, mesero, negocio):
    respuesta = cliente_api_autenticado(mesero).get(URL_MI_NEGOCIO)

    assert respuesta.status_code == 200
    assert respuesta.data["id"] == negocio.id


def test_el_staff_no_tiene_un_negocio_que_mirar(cliente_api_autenticado, staff):
    respuesta = cliente_api_autenticado(staff).get(URL_MI_NEGOCIO)

    assert respuesta.status_code == 403


# --------------------------------------------------------------------------- #
# Resumen de ventas por canal
# --------------------------------------------------------------------------- #
def test_el_resumen_de_ventas_es_del_administrador(cliente_api_autenticado, cajero):
    respuesta = cliente_api_autenticado(cajero).get(URL_RESUMEN)

    assert respuesta.status_code == 403


def test_el_resumen_de_ventas_suma_los_dos_canales(cliente_api_autenticado, administrador, negocio):
    bodega = FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(negocio=negocio, precio_mayorista=Decimal("3500.00")),
    )
    tienda = FabricaDeClienteDistribucion(negocio=negocio)
    pedidos_de_mayoreo.crear_pedido(
        cliente_distribucion_id=tienda.id,
        lineas=[LineaDePedidoDTO(producto_id=bodega.producto_id, cantidad=Decimal("10.00"))],
        usuario_id=administrador.id,
        negocio_id=negocio.id,
    )

    respuesta = cliente_api_autenticado(administrador).get(URL_RESUMEN)

    assert respuesta.status_code == 200
    assert respuesta.data["vendido_total"] == "35000.00"
    assert [canal["canal"] for canal in respuesta.data["canales"]] == ["bar", "mayoreo"]


def test_el_resumen_acepta_un_rango_de_fechas(cliente_api_autenticado, administrador):
    ayer = (timezone.localdate() - timedelta(days=1)).isoformat()

    respuesta = cliente_api_autenticado(administrador).get(
        URL_RESUMEN, {"desde": ayer, "hasta": ayer}
    )

    assert respuesta.status_code == 200
    assert respuesta.data["desde"] == ayer


def test_un_rango_al_reves_devuelve_400(cliente_api_autenticado, administrador):
    hoy = timezone.localdate()

    respuesta = cliente_api_autenticado(administrador).get(
        URL_RESUMEN,
        {"desde": hoy.isoformat(), "hasta": (hoy - timedelta(days=3)).isoformat()},
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "rango_de_fechas_invalido"

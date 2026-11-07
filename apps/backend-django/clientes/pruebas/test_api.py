"""Pruebas de los endpoints de clientes.

El reparto de permisos es lo propio de esta app: el mesero y el cajero
registran y buscan clientes toda la noche, pero desactivar una ficha es de
administrador.
"""

import pytest
from django.urls import reverse

from clientes.models import Cliente
from clientes.pruebas.fabricas import FabricaDeCliente

pytestmark = pytest.mark.django_db

URL_CLIENTES = reverse("clientes:cliente-list")
URL_POR_DOCUMENTO = reverse("clientes:cliente-por-documento")

FICHA = {
    "tipo_documento": Cliente.TipoDocumento.CEDULA,
    "numero_documento": "1020304050",
    "nombre": "Ana",
    "apellido": "Pérez",
    "fecha_nacimiento": "1995-06-15",
}


# --------------------------------------------------------------------------- #
# Permisos
# --------------------------------------------------------------------------- #
def test_sin_iniciar_sesion_no_se_ven_los_clientes(cliente_api):
    respuesta = cliente_api.get(URL_CLIENTES)

    assert respuesta.status_code == 401


def test_un_mesero_si_puede_registrar_clientes(cliente_api_autenticado, mesero):
    """Es lo que hace en la barra: registrar a quien llega."""
    respuesta = cliente_api_autenticado(mesero).post(URL_CLIENTES, FICHA, format="json")

    assert respuesta.status_code == 201


def test_un_mesero_no_puede_desactivar_una_ficha(cliente_api_autenticado, mesero, negocio):
    ficha = FabricaDeCliente(negocio=negocio)

    respuesta = cliente_api_autenticado(mesero).post(
        reverse("clientes:cliente-desactivacion", args=[ficha.id])
    )

    assert respuesta.status_code == 403
    ficha.refresh_from_db()
    assert ficha.activo is True


def test_un_administrador_si_puede_desactivarla(cliente_api_autenticado, administrador, negocio):
    ficha = FabricaDeCliente(negocio=negocio)

    respuesta = cliente_api_autenticado(administrador).post(
        reverse("clientes:cliente-desactivacion", args=[ficha.id])
    )

    assert respuesta.status_code == 200
    assert respuesta.data["activo"] is False


# --------------------------------------------------------------------------- #
# Aislamiento entre negocios
# --------------------------------------------------------------------------- #
def test_el_listado_solo_trae_las_fichas_del_negocio(cliente_api_autenticado, cajero, negocio):
    FabricaDeCliente.create_batch(2, negocio=negocio)
    FabricaDeCliente()  # de otro negocio

    respuesta = cliente_api_autenticado(cajero).get(URL_CLIENTES)

    assert respuesta.data["count"] == 2


def test_pedir_la_ficha_de_otro_negocio_devuelve_404(cliente_api_autenticado, cajero):
    ajena = FabricaDeCliente()

    respuesta = cliente_api_autenticado(cajero).get(
        reverse("clientes:cliente-detail", args=[ajena.id])
    )

    assert respuesta.status_code == 404


def test_el_historial_de_otro_negocio_tampoco_se_ve(cliente_api_autenticado, cajero):
    ajena = FabricaDeCliente()

    respuesta = cliente_api_autenticado(cajero).get(
        reverse("clientes:cliente-historial", args=[ajena.id])
    )

    assert respuesta.status_code == 404


# --------------------------------------------------------------------------- #
# Registro y búsqueda
# --------------------------------------------------------------------------- #
def test_la_respuesta_avisa_de_que_es_menor_de_edad(cliente_api_autenticado, mesero):
    ficha = FICHA | {"fecha_nacimiento": "2012-01-01", "numero_documento": "1122334455"}

    respuesta = cliente_api_autenticado(mesero).post(URL_CLIENTES, ficha, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["es_menor_de_edad"] is True


def test_el_documento_repetido_devuelve_409(cliente_api_autenticado, mesero, negocio):
    FabricaDeCliente(negocio=negocio, numero_documento="1020304050")

    respuesta = cliente_api_autenticado(mesero).post(URL_CLIENTES, FICHA, format="json")

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "documento_duplicado"


def test_buscar_por_documento_devuelve_la_ficha(cliente_api_autenticado, cajero, negocio):
    ficha = FabricaDeCliente(negocio=negocio, numero_documento="1020304050")

    respuesta = cliente_api_autenticado(cajero).get(
        URL_POR_DOCUMENTO,
        {"tipo_documento": Cliente.TipoDocumento.CEDULA, "numero_documento": "1020304050"},
    )

    assert respuesta.status_code == 200
    assert respuesta.data["id"] == ficha.id


def test_buscar_un_documento_que_no_existe_devuelve_404(cliente_api_autenticado, cajero):
    respuesta = cliente_api_autenticado(cajero).get(
        URL_POR_DOCUMENTO,
        {"tipo_documento": Cliente.TipoDocumento.CEDULA, "numero_documento": "0000000000"},
    )

    assert respuesta.status_code == 404


def test_una_ficha_sin_historial_devuelve_una_lista_vacia(cliente_api_autenticado, cajero, negocio):
    """El estado vacío también se contempla: una lista sin él se siente rota."""
    ficha = FabricaDeCliente(negocio=negocio)

    respuesta = cliente_api_autenticado(cajero).get(
        reverse("clientes:cliente-historial", args=[ficha.id])
    )

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0

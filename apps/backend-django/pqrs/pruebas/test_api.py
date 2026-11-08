"""Pruebas de radicación, historial y aislamiento de PQR."""

import pytest
from django.urls import reverse

from clientes.pruebas.fabricas import FabricaDeCliente
from pqrs.models import Pqr, PqrSeguimiento
from usuarios.pruebas.fabricas import FabricaDeUsuario

pytestmark = pytest.mark.django_db

URL_PQRS = reverse("pqrs:pqr-list")
DATOS_PQR = {
    "nombre_solicitante": "Tienda La Esquina",
    "documento_solicitante": "900123456",
    "telefono_solicitante": "3101234567",
    "correo_solicitante": "",
    "tipo": "reclamo",
    "ambito": "productos",
    "canal": "presencial",
    "asunto": "Producto averiado",
    "descripcion": "Llegaron dos unidades quebradas.",
}


def test_sin_autenticacion_no_se_pueden_consultar_pqrs(cliente_api):
    respuesta = cliente_api.get(URL_PQRS)

    assert respuesta.status_code == 401


def test_radicar_pqr_crea_radicado_y_evento_inicial(
    cliente_api_autenticado, cajero, negocio
):
    respuesta = cliente_api_autenticado(cajero).post(URL_PQRS, DATOS_PQR, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["radicado"].startswith("PQR-")
    assert respuesta.data["estado"] == Pqr.Estado.RADICADA
    assert respuesta.data["seguimientos"][0]["tipo"] == PqrSeguimiento.Tipo.RADICACION
    assert Pqr.objects.filter(negocio=negocio).count() == 1


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre_solicitante", "  "),
        ("nombre_solicitante", "AB"),
        ("asunto", "abc"),
        ("descripcion", "Muy corto"),
        ("correo_solicitante", "correo-invalido"),
    ],
)
def test_radicar_pqr_rechaza_datos_invalidos(
    cliente_api_autenticado, cajero, campo, valor
):
    respuesta = cliente_api_autenticado(cajero).post(
        URL_PQRS, DATOS_PQR | {campo: valor}, format="json"
    )

    assert respuesta.status_code == 400
    assert campo in respuesta.data["error"]["detalles"]


def test_listado_y_resumen_solo_muestran_pqrs_del_negocio(
    cliente_api_autenticado, cajero, negocio
):
    cliente = cliente_api_autenticado(cajero)
    cliente.post(URL_PQRS, DATOS_PQR, format="json")
    usuario_ajeno = FabricaDeUsuario()
    ajena = Pqr.objects.create(
        negocio=usuario_ajeno.negocio,
        usuario_registro=usuario_ajeno,
        estado=Pqr.Estado.CERRADA,
        **DATOS_PQR,
    )
    PqrSeguimiento.objects.create(
        negocio=usuario_ajeno.negocio,
        pqr=ajena,
        tipo=PqrSeguimiento.Tipo.RADICACION,
        contenido="Solicitud radicada.",
        usuario=usuario_ajeno,
    )

    listado = cliente.get(URL_PQRS)
    resumen = cliente.get(reverse("pqrs:pqr-resumen"))

    assert listado.data["count"] == 1
    assert resumen.data == {"total": 1, "servicio": 0, "productos": 1, "pendientes": 1}


def test_no_se_puede_enlazar_un_cliente_de_otro_negocio(
    cliente_api_autenticado, cajero
):
    cliente_ajeno = FabricaDeCliente()
    datos = DATOS_PQR | {"cliente": cliente_ajeno.id}

    respuesta = cliente_api_autenticado(cajero).post(URL_PQRS, datos, format="json")

    assert respuesta.status_code == 400
    assert Pqr.objects.count() == 0


def test_documento_coincidente_enlaza_el_cliente_y_conserva_su_snapshot(
    cliente_api_autenticado, cajero, negocio
):
    ficha = FabricaDeCliente(
        negocio=negocio,
        numero_documento=DATOS_PQR["documento_solicitante"],
        nombre="Tienda",
        apellido="La Esquina",
    )

    respuesta = cliente_api_autenticado(cajero).post(URL_PQRS, DATOS_PQR, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["cliente_id"] == ficha.id
    assert respuesta.data["nombre_solicitante"] == "Tienda La Esquina"


def test_respuesta_cambia_a_respondida_y_se_guarda_en_historial(
    cliente_api_autenticado, cajero
):
    cliente = cliente_api_autenticado(cajero)
    pqr = cliente.post(URL_PQRS, DATOS_PQR, format="json").data

    respuesta = cliente.post(
        reverse("pqrs:pqr-seguimientos", args=[pqr["id"]]),
        {"tipo": "respuesta", "contenido": "Repondremos las unidades en el próximo despacho."},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["estado"] == Pqr.Estado.RESPONDIDA
    assert respuesta.data["seguimientos"][-1]["visible_solicitante"] is True
    assert respuesta.data["seguimientos"][-1]["contenido"].startswith("Repondremos")


def test_filtrar_pqrs_con_o_sin_respuesta(cliente_api_autenticado, cajero):
    cliente = cliente_api_autenticado(cajero)
    pqr_con_respuesta = cliente.post(URL_PQRS, DATOS_PQR, format="json").data
    pqr_sin_respuesta = cliente.post(
        URL_PQRS,
        DATOS_PQR | {"asunto": "Otra solicitud pendiente"},
        format="json",
    ).data
    cliente.post(
        reverse("pqrs:pqr-seguimientos", args=[pqr_con_respuesta["id"]]),
        {"tipo": "respuesta", "contenido": "Respuesta de prueba registrada."},
        format="json",
    )

    filtradas_con_respuesta = cliente.get(URL_PQRS, {"respuesta": "si"})
    filtradas_sin_respuesta = cliente.get(URL_PQRS, {"respuesta": "no"})

    assert [pqr["id"] for pqr in filtradas_con_respuesta.data["results"]] == [
        pqr_con_respuesta["id"]
    ]
    assert [pqr["id"] for pqr in filtradas_sin_respuesta.data["results"]] == [
        pqr_sin_respuesta["id"]
    ]


def test_pqr_se_puede_asignar_al_usuario_actual(
    cliente_api_autenticado, cajero
):
    cliente = cliente_api_autenticado(cajero)
    pqr = cliente.post(URL_PQRS, DATOS_PQR, format="json").data

    respuesta = cliente.post(
        reverse("pqrs:pqr-seguimientos", args=[pqr["id"]]),
        {"tipo": "asignacion"},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["responsable_id"] == cajero.id
    assert respuesta.data["responsable_nombre"] == "Ana Ríos"
    assert respuesta.data["seguimientos"][-1]["tipo"] == PqrSeguimiento.Tipo.ASIGNACION


def test_cerrar_pqr_guarda_fecha_y_movimiento_de_estado(
    cliente_api_autenticado, administrador
):
    cliente = cliente_api_autenticado(administrador)
    pqr = cliente.post(URL_PQRS, DATOS_PQR, format="json").data

    respuesta = cliente.post(
        reverse("pqrs:pqr-seguimientos", args=[pqr["id"]]),
        {"tipo": "cambio_estado", "nuevo_estado": "cerrada", "contenido": "Caso finalizado."},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["estado"] == Pqr.Estado.CERRADA
    assert respuesta.data["fecha_cierre"] is not None
    assert respuesta.data["seguimientos"][-1]["estado_anterior"] == Pqr.Estado.RADICADA


def test_un_usuario_no_puede_consultar_pqr_de_otro_negocio(
    cliente_api_autenticado, cajero
):
    usuario_ajeno = FabricaDeUsuario()
    ajena = Pqr.objects.create(
        negocio=usuario_ajeno.negocio,
        usuario_registro=usuario_ajeno,
        **DATOS_PQR,
    )

    respuesta = cliente_api_autenticado(cajero).get(
        reverse("pqrs:pqr-detail", args=[ajena.id])
    )

    assert respuesta.status_code == 404

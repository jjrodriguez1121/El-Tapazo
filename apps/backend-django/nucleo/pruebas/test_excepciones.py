"""Pruebas del manejador global de errores.

Que todos los errores salgan con la misma forma es el contrato con el
frontend: si se rompe, se rompe el manejo de errores de toda la aplicación.
"""

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError

from nucleo.excepciones import ErrorDeNegocio
from nucleo.excepciones.manejador import manejador_de_excepciones


class ErrorDePrueba(ErrorDeNegocio):
    mensaje = "Algo no cuadra."
    codigo = "algo_no_cuadra"
    status_http = status.HTTP_409_CONFLICT


def test_un_error_de_negocio_sale_con_su_codigo_y_su_estado():
    respuesta = manejador_de_excepciones(ErrorDePrueba(), {})

    assert respuesta.status_code == 409
    assert respuesta.data == {"error": {"codigo": "algo_no_cuadra", "mensaje": "Algo no cuadra."}}


def test_los_detalles_viajan_dentro_del_error():
    respuesta = manejador_de_excepciones(ErrorDePrueba(disponible=3), {})

    assert respuesta.data["error"]["detalles"] == {"disponible": 3}


def test_el_mensaje_se_puede_concretar_al_lanzar():
    respuesta = manejador_de_excepciones(ErrorDePrueba("Ese pedido ya se anuló."), {})

    assert respuesta.data["error"]["mensaje"] == "Ese pedido ya se anuló."


def test_un_error_de_serializer_sale_con_la_misma_forma():
    respuesta = manejador_de_excepciones(
        ValidationError({"cantidad": ["Este campo es obligatorio."]}), {}
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "datos_invalidos"
    assert respuesta.data["error"]["detalles"] == {"cantidad": ["Este campo es obligatorio."]}


def test_un_404_de_drf_tambien_se_traduce():
    respuesta = manejador_de_excepciones(NotFound(), {})

    assert respuesta.status_code == 404
    assert respuesta.data["error"]["codigo"] == "no_encontrado"


def test_lo_inesperado_no_se_disfraza_de_error_controlado():
    """Un fallo nuestro sube y queda en los logs: nunca se convierte en un 400."""
    assert manejador_de_excepciones(ZeroDivisionError(), {}) is None

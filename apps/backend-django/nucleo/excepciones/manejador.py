"""Manejador global de errores de la API.

Todos los errores salen con la misma forma, para que el frontend escriba el
manejo una sola vez:

    {"error": {"codigo": "...", "mensaje": "...", "detalles": {...}}}

El `codigo` es lo estable: el frontend reacciona a él, nunca al texto del
mensaje, que puede cambiar sin previo aviso.

Se conecta en `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Ninguna vista arma
respuestas de error a mano.
"""

import logging
from typing import Any

from django.core.exceptions import ValidationError as ErrorDeValidacionDeDjango
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as manejador_de_drf

from nucleo.excepciones.base import ErrorDeNegocio

logger = logging.getLogger(__name__)

# Código estable por estado HTTP, para lo que no es un error de negocio nuestro.
CODIGOS_POR_ESTADO = {
    status.HTTP_400_BAD_REQUEST: ("datos_invalidos", "Revisa los datos enviados."),
    status.HTTP_401_UNAUTHORIZED: ("no_autenticado", "Necesitas iniciar sesión."),
    status.HTTP_403_FORBIDDEN: ("sin_permiso", "No tienes permiso para hacer esto."),
    status.HTTP_404_NOT_FOUND: ("no_encontrado", "No se encontró lo que buscas."),
    status.HTTP_405_METHOD_NOT_ALLOWED: ("metodo_no_permitido", "Esa operación no existe aquí."),
    status.HTTP_409_CONFLICT: ("conflicto", "La operación no se puede hacer en este estado."),
    status.HTTP_429_TOO_MANY_REQUESTS: (
        "demasiadas_peticiones",
        "Demasiados intentos. Espera un momento y vuelve a intentarlo.",
    ),
}


def manejador_de_excepciones(exc: Exception, contexto: dict) -> Response | None:
    """Traduce cualquier excepción a la respuesta de error del proyecto."""
    if isinstance(exc, ErrorDeNegocio):
        return _respuesta(exc.codigo, exc.mensaje, exc.detalles, exc.status_http)

    if isinstance(exc, ErrorDeValidacionDeDjango):
        # Lo que lanzan los validadores de Django (contraseñas, `full_clean`).
        return _respuesta(
            "datos_invalidos",
            "Revisa los datos enviados.",
            {"errores": list(exc.messages)},
            status.HTTP_400_BAD_REQUEST,
        )

    respuesta = manejador_de_drf(exc, contexto)
    if respuesta is None:
        # No lo esperábamos: que suba y quede en los logs con su traza.
        logger.exception("Error no controlado en %s", contexto.get("request"))
        return None

    codigo, mensaje = CODIGOS_POR_ESTADO.get(
        respuesta.status_code, ("error", "No se pudo completar la operación.")
    )
    return _respuesta(codigo, mensaje, _detalles_de_drf(respuesta.data), respuesta.status_code)


def _detalles_de_drf(datos: Any) -> dict:
    """Deja los errores de un serializer como {campo: [mensajes]}."""
    if isinstance(datos, dict):
        # `detail` es el mensaje suelto de las excepciones de DRF; ya va en `mensaje`.
        return {campo: valor for campo, valor in datos.items() if campo != "detail"}
    if isinstance(datos, list):
        return {"errores": datos}
    return {}


def _respuesta(codigo: str, mensaje: str, detalles: dict, estado: int) -> Response:
    cuerpo = {"error": {"codigo": codigo, "mensaje": mensaje}}
    if detalles:
        cuerpo["error"]["detalles"] = detalles
    return Response(cuerpo, status=estado)

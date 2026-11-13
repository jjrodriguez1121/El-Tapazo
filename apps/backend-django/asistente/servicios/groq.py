"""Cliente mínimo de la API de Groq (compatible con la de OpenAI).

Se usa la librería estándar para no sumar una dependencia por una sola
petición HTTP. La clave vive en el `.env` del backend (`GROQ_API_KEY`) y nunca
sale hacia el navegador: el frontend habla con nuestra API y esta con Groq.
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

URL_COMPLETADOS = "https://api.groq.com/openai/v1/chat/completions"


class ErrorDelAsistente(Exception):
    """Algo falló al hablar con Groq; el mensaje se puede mostrar al usuario."""


def completar(
    mensajes: list[dict], *, respuesta_json: bool = False, temperatura: float = 0.3
) -> str:
    """Envía la conversación a Groq y devuelve el texto de la respuesta."""
    clave = settings.GROQ_API_KEY
    if not clave:
        raise ErrorDelAsistente(
            "El asistente no está configurado: falta GROQ_API_KEY en el backend."
        )

    cuerpo = {
        "model": settings.GROQ_MODELO,
        "messages": mensajes,
        "temperature": temperatura,
    }
    if respuesta_json:
        cuerpo["response_format"] = {"type": "json_object"}

    peticion = urllib.request.Request(
        URL_COMPLETADOS,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
            # Sin User-Agent propio, Cloudflare rechaza el de urllib.
            "User-Agent": "el-tapaso-backend/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=settings.GROQ_TIEMPO_LIMITE) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")[:500]
        logger.warning("Groq respondió %s: %s", error.code, detalle)
        if error.code == 429:
            raise ErrorDelAsistente(
                "El asistente está saturado. Intenta de nuevo en un momento."
            ) from error
        if error.code in (401, 403):
            raise ErrorDelAsistente("La clave de Groq no es válida o fue revocada.") from error
        raise ErrorDelAsistente("El asistente no pudo responder. Intenta de nuevo.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        logger.warning("No se pudo contactar a Groq: %s", error)
        raise ErrorDelAsistente(
            "No fue posible contactar al asistente. Revisa la conexión."
        ) from error

    try:
        return datos["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError) as error:
        raise ErrorDelAsistente("El asistente devolvió una respuesta inesperada.") from error

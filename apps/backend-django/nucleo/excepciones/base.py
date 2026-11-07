"""Excepción base de la que heredan los errores esperados de todo el proyecto.

Un `ErrorDeNegocio` es lo que pasa cuando alguien intenta algo que las reglas
no permiten: una invitación vencida, unas existencias insuficientes. No es un
fallo del sistema, es una respuesta prevista.

Los servicios lanzan estas excepciones y **no saben nada de HTTP**: el
manejador global (`nucleo/excepciones/manejador.py`) las traduce a la
respuesta correcta.
"""

from typing import Any


class ErrorDeNegocio(Exception):
    """Error esperado: el usuario hizo algo que las reglas no permiten."""

    mensaje = "Ocurrió un error de negocio."
    codigo = "error_de_negocio"
    status_http = 400

    def __init__(self, mensaje: str | None = None, **detalles: Any) -> None:
        self.mensaje = mensaje or self.mensaje
        self.detalles = detalles
        super().__init__(self.mensaje)

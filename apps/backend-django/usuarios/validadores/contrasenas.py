"""Validación de contraseñas, en un solo sitio.

La usan los tres caminos por los que alguien elige una contraseña: aceptar la
invitación, restablecerla desde el enlace y cambiarla desde la aplicación.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ErrorDeValidacionDeDjango

from usuarios.excepciones import ContrasenaInsegura
from usuarios.models import Usuario

MENSAJE_SIN_LETRAS = "La contraseña debe tener al menos una letra."
MENSAJE_SIN_NUMEROS = "La contraseña debe tener al menos un número."


def validar_contrasena(*, contrasena: str, usuario: Usuario | None = None) -> None:
    """Aplica los `AUTH_PASSWORD_VALIDATORS` del proyecto.

    El usuario se pasa cuando existe porque es parte de la firma de los
    validadores de Django, aunque hoy ninguna regla lo mira.

    Raises:
        ContrasenaInsegura: con la lista de motivos en `detalles`.
    """
    try:
        validate_password(contrasena, user=usuario)
    except ErrorDeValidacionDeDjango as exc:
        raise ContrasenaInsegura(errores=list(exc.messages)) from exc


class ValidadorDeLetrasYNumeros:
    """Exige al menos una letra y al menos un número.

    Es un validador de Django: se registra en `AUTH_PASSWORD_VALIDATORS`, y
    `validate` y `get_help_text` son los nombres que Django busca. Si faltan
    las dos cosas, devuelve los dos motivos a la vez, para que el formulario no
    los descubra de uno en uno.
    """

    def validate(self, password: str, user: Usuario | None = None) -> None:
        motivos = []
        if not any(caracter.isalpha() for caracter in password):
            motivos.append(ErrorDeValidacionDeDjango(MENSAJE_SIN_LETRAS, code="sin_letras"))
        if not any(caracter.isdecimal() for caracter in password):
            motivos.append(ErrorDeValidacionDeDjango(MENSAJE_SIN_NUMEROS, code="sin_numeros"))
        if motivos:
            raise ErrorDeValidacionDeDjango(motivos)

    def get_help_text(self) -> str:
        return "La contraseña debe tener al menos una letra y un número."

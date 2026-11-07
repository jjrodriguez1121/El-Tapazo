"""Tokens de un solo uso que viajan por correo.

Hay dos mecanismos distintos, y la diferencia es a propósito:

* La **invitación** guarda el suyo en la base de datos
  (`invitaciones.hash_token`): existe antes que el usuario, un administrador
  tiene que poder listarla y revocarla, y de ella se guarda solo el hash — si
  alguien lee la base de datos, no puede usar la invitación.

* La **recuperación de contraseña** y la **verificación de correo** no guardan
  nada. Son tokens firmados que llevan dentro el estado que los invalida: el
  de recuperación deja de servir en cuanto la contraseña cambia, y el de
  verificación en cuanto el correo queda verificado. Sin tabla nueva, sin
  filas caducadas que limpiar y sin un estado más que se pueda desincronizar.
"""

import hashlib
import secrets

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# 32 bytes al azar: suficiente para que adivinarlo no sea una estrategia.
BYTES_DEL_TOKEN = 32


def generar_token_de_invitacion() -> tuple[str, str]:
    """Devuelve `(token, hash)`. El token va al correo; el hash, a la base."""
    token = secrets.token_urlsafe(BYTES_DEL_TOKEN)
    return token, calcular_hash(token)


def calcular_hash(token: str) -> str:
    """SHA-256 en hexadecimal: 64 caracteres, los de `invitaciones.hash_token`."""
    return hashlib.sha256(token.encode()).hexdigest()


class _GeneradorDeVerificacionDeCorreo(PasswordResetTokenGenerator):
    """Token del enlace de verificación de correo.

    Cambia respecto al de recuperación en dos cosas: la sal, para que un token
    no sirva para lo otro, y lo que entra en la firma. Aquí entra
    `correo_verificado_en`, que es lo que hace el enlace de un solo uso: en
    cuanto se verifica, la fecha deja de estar vacía y el token ya no cuadra.
    """

    key_salt = "usuarios.verificacion-de-correo"

    def _make_hash_value(self, usuario, marca_de_tiempo: int) -> str:
        verificado_en = "" if usuario.correo_verificado_en is None else usuario.correo_verificado_en
        return f"{usuario.pk}{usuario.correo}{verificado_en}{marca_de_tiempo}"


# El de recuperación es el de Django tal cual: firma la contraseña actual y la
# fecha del último acceso, así que el enlace muere al cambiar la contraseña.
token_de_recuperacion = PasswordResetTokenGenerator()
token_de_verificacion = _GeneradorDeVerificacionDeCorreo()


def codificar_id(usuario_id: int) -> str:
    """El `uid` que acompaña al token en el enlace."""
    return urlsafe_base64_encode(force_bytes(usuario_id))


def decodificar_id(uid: str) -> int | None:
    """Devuelve el id del enlace, o `None` si viene manipulado."""
    try:
        return int(force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, OverflowError):
        return None

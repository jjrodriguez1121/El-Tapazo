"""Autenticación del lector de la puerta.

El punto de control **no lleva la sesión de una persona**, y es la razón de que
exista `dispositivos_nfc`: un aparato colgado en la puerta de un bar lo desarma
cualquiera, y lo que se saque de ahí no puede ser una credencial de cajero. Con
un token propio, si alguien abre la caja se revoca ese y ya.

El token viaja en la cabecera y de él solo se guarda el hash, así que aquí se
hashea lo que llega y se busca por el hash — igual que con las invitaciones.

Se devuelve `(usuario anónimo, dispositivo)` a propósito: `request.user` sigue
sin ser nadie, y lo que autoriza es `request.auth`. Así ningún permiso de rol
puede confundir a un aparato con una persona.
"""

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from eventos.models import DispositivoNfc
from eventos.repositorios import pulseras as repositorio
from usuarios.tokens import calcular_hash

PREFIJO = b"dispositivo"


class AutenticacionDeDispositivo(BaseAuthentication):
    """`Authorization: Dispositivo <token>`."""

    def authenticate(self, request) -> tuple[AnonymousUser, DispositivoNfc] | None:
        partes = get_authorization_header(request).split()
        if not partes or partes[0].lower() != PREFIJO:
            # No es para nosotros: que lo intente otra clase de autenticación.
            return None
        if len(partes) != 2:
            raise AuthenticationFailed("La cabecera de autorización está mal formada.")

        dispositivo = repositorio.obtener_dispositivo_por_hash(
            hash_token=calcular_hash(partes[1].decode())
        )
        if dispositivo is None:
            # Mismo mensaje para un token falso y para uno revocado: distinguir
            # los dos casos le diría a quien prueba tokens cuánto se acercó.
            raise AuthenticationFailed("El dispositivo no está autorizado.")

        repositorio.marcar_uso(dispositivo_id=dispositivo.id)
        return AnonymousUser(), dispositivo

    def authenticate_header(self, request) -> str:
        return "Dispositivo"

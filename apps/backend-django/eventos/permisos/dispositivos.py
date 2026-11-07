"""Permiso del punto de control."""

from rest_framework.permissions import BasePermission

from eventos.models import DispositivoNfc


class EsDispositivoNfc(BasePermission):
    """Solo un lector dado de alta y activo.

    Mira `request.auth` y no `request.user`: quien consulta es un aparato, no
    una persona, y mezclarlos dejaría que un permiso de rol lo diera por bueno.
    """

    message = "Este endpoint es para los lectores de la puerta."

    def has_permission(self, request, view) -> bool:
        return isinstance(request.auth, DispositivoNfc)

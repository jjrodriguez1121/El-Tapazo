"""Quién administra los negocios: el staff de la plataforma y nadie más.

Es el permiso opuesto a los de `nucleo/permisos/`: aquellos exigen **tener** un
negocio, y este exige estar por encima de todos. Vive aquí y no en `nucleo`
porque solo lo usa esta app: dar de alta negocios es lo único que el staff hace
en la API.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class EsStaffDePlataforma(BasePermission):
    """Solo el staff de la plataforma (`is_superuser`).

    El staff no pertenece a ningún negocio, así que ninguno de los permisos por
    rol le sirve: todos exigen `negocio_id`.
    """

    message = "Esto solo lo puede hacer el staff de la plataforma."

    def has_permission(self, request: Request, view: APIView) -> bool:
        usuario = request.user
        return bool(usuario.is_authenticated and usuario.is_superuser)

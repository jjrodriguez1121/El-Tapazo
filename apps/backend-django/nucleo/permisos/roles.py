"""Permisos por rol, compartidos por todas las apps.

Los tres roles del sistema son `admin`, `cajero` y `mesero`, y quién puede
hacer qué está fijado en el plan de negocio (`varios/planes/`, decisión 6).
Aquí se traduce esa matriz a clases de DRF, en un solo sitio: si mañana el
cajero necesita hacer algo más, se cambia aquí y no en catorce vistas.

Las tres exigen además que la persona **pertenezca a un negocio**. Eso deja
fuera al staff de la plataforma (`is_superuser`, sin negocio), que da de alta
negocios desde la terminal y no opera el día a día de ninguno.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from usuarios.models import Rol


class _PermisoDeRol(BasePermission):
    """Base de los permisos por rol. No se usa directamente."""

    roles: tuple[str, ...] = ()
    message = "No tienes permiso para hacer esto."

    def has_permission(self, request: Request, view: APIView) -> bool:
        usuario = request.user
        return bool(usuario.is_authenticated and usuario.negocio_id and usuario.rol in self.roles)


class EsAdministrador(_PermisoDeRol):
    """Solo el administrador del negocio.

    Es lo que protege el catálogo, el inventario y el canal mayorista: cosas
    que cambian lo que el resto del equipo ve, no la operación de una noche.
    """

    roles = (Rol.ADMINISTRADOR,)
    message = "Solo un administrador puede hacer esto."


class EsCajeroOAdministrador(_PermisoDeRol):
    """El cajero y el administrador.

    Todo lo que toca dinero: cobrar, cerrar cuentas, liberar pulseras y abrir
    o cerrar la caja. El mesero toma comandas, pero no cobra.
    """

    roles = (Rol.ADMINISTRADOR, Rol.CAJERO)
    message = "Solo un cajero o un administrador pueden hacer esto."


class EsDelEquipo(_PermisoDeRol):
    """Cualquiera del negocio: administrador, cajero o mesero.

    La operación de la barra —abrir grupos y cuentas, asignar pulseras, tomar
    y entregar comandas— la hacen los tres.
    """

    roles = (Rol.ADMINISTRADOR, Rol.CAJERO, Rol.MESERO)
    message = "Necesitas pertenecer a un negocio para hacer esto."

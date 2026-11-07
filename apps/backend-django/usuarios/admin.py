from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AdminDeUsuarioBase

from .models import Invitacion, Usuario


@admin.register(Usuario)
class UsuarioAdmin(AdminDeUsuarioBase):
    """Admin ajustado a que el identificador es el correo, no un `username`."""

    ordering = ("correo",)
    list_display = ("correo", "nombre_completo", "negocio", "rol", "activo", "correo_verificado_en")
    list_filter = ("activo", "rol", "negocio", "is_superuser")
    search_fields = ("correo", "nombre", "apellido")

    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        ("Datos personales", {"fields": ("nombre", "apellido", "telefono")}),
        ("Negocio", {"fields": ("negocio", "rol")}),
        (
            "Permisos",
            {"fields": ("activo", "es_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Fechas",
            {
                "fields": ("last_login", "fecha_alta", "correo_verificado_en"),
                "description": (
                    "Sin «correo verificado en» la persona no puede iniciar sesión. "
                    "Se llena sola al aceptar la invitación o al abrir el enlace de "
                    "verificación."
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "correo",
                    "nombre",
                    "apellido",
                    "negocio",
                    "rol",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    """Solo para mirar.

    Crear una invitación desde aquí no serviría: el token se genera y se
    envía en `servicios/invitaciones.py`, y de él solo se guarda el hash.
    Para invitar al primer administrador de un negocio está el comando
    `./dev.sh manage invitar_administrador`; el resto del equipo se invita
    desde la aplicación.
    """

    list_display = ("correo", "negocio", "rol", "expira_en", "aceptada_en")
    list_filter = ("negocio", "rol")
    search_fields = ("correo",)
    readonly_fields = ("hash_token", "aceptada_en", "aceptada_por")

    def has_add_permission(self, request) -> bool:
        """Crear una invitación a mano dejaría una fila sin enlace que enviar."""
        return False

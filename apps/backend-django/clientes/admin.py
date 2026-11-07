from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "apellido",
        "tipo_documento",
        "numero_documento",
        "negocio",
        "telefono",
        "activo",
    )
    list_filter = ("negocio", "activo", "tipo_documento")
    search_fields = ("nombre", "apellido", "numero_documento", "correo")

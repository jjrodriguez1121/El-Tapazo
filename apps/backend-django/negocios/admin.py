from django.contrib import admin

from .models import Negocio


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ("nombre_comercial", "nit", "estado", "creado_en")
    list_filter = ("estado",)
    search_fields = ("nombre_comercial", "nit")

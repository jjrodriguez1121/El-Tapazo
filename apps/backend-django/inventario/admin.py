from django.contrib import admin

from .models import Existencia, MovimientoInventario, Ubicacion


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "negocio", "direccion", "activa")
    list_filter = ("negocio", "tipo", "activa")
    search_fields = ("nombre", "direccion")


@admin.register(Existencia)
class ExistenciaAdmin(admin.ModelAdmin):
    list_display = ("producto", "ubicacion", "cantidad_disponible", "negocio")
    list_filter = ("negocio", "ubicacion")
    search_fields = ("producto__sku", "producto__nombre")
    # El saldo lo mueven los movimientos de inventario, no el panel: editarlo a
    # mano dejaría la tabla y el kardex diciendo cosas distintas.
    readonly_fields = ("cantidad_disponible",)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo", "producto", "ubicacion", "cantidad", "usuario", "negocio")
    list_filter = ("negocio", "tipo", "ubicacion")
    search_fields = ("producto__sku", "producto__nombre", "nota")
    date_hierarchy = "fecha"
    # El kardex no se edita ni se borra: un movimiento equivocado se corrige
    # con un movimiento contrario, y los dos quedan.
    readonly_fields = tuple(campo.name for campo in MovimientoInventario._meta.fields)

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

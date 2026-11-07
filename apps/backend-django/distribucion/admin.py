from django.contrib import admin

from .models import (
    ClienteDistribucion,
    DetallePedidoDistribucion,
    PagoDistribucion,
    PedidoDistribucion,
)


@admin.register(ClienteDistribucion)
class ClienteDistribucionAdmin(admin.ModelAdmin):
    list_display = (
        "razon_social",
        "nit",
        "negocio",
        "ciudad",
        "telefono",
        "dias_credito",
        "activo",
    )
    list_filter = ("negocio", "activo", "ciudad")
    search_fields = ("razon_social", "nit", "nombre_contacto")


class DetallePedidoDistribucionInline(admin.TabularInline):
    """Las líneas se editan dentro de su pedido: solas no significan nada."""

    model = DetallePedidoDistribucion
    extra = 0
    autocomplete_fields = ("producto",)


@admin.register(PedidoDistribucion)
class PedidoDistribucionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "negocio",
        "cliente_distribucion",
        "usuario",
        "estado",
        "fecha_pedido",
        "fecha_entrega",
    )
    list_filter = ("negocio", "estado")
    search_fields = ("id", "cliente_distribucion__razon_social", "cliente_distribucion__nit")
    date_hierarchy = "fecha_pedido"
    autocomplete_fields = ("cliente_distribucion", "usuario")
    inlines = [DetallePedidoDistribucionInline]


@admin.register(DetallePedidoDistribucion)
class DetallePedidoDistribucionAdmin(admin.ModelAdmin):
    list_display = ("pedido_distribucion", "producto", "cantidad", "precio_unitario")
    list_filter = ("negocio",)
    search_fields = ("producto__nombre", "producto__sku")
    autocomplete_fields = ("pedido_distribucion", "producto")


@admin.register(PagoDistribucion)
class PagoDistribucionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "negocio", "pedido_distribucion", "monto", "metodo", "fecha")
    list_filter = ("negocio", "metodo")
    search_fields = ("referencia_transaccion", "pedido_distribucion__id")
    date_hierarchy = "fecha"
    autocomplete_fields = ("pedido_distribucion", "recibido_por")

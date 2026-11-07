from django.contrib import admin

from .models import Categoria, Producto, ProductoProveedor, Proveedor


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "negocio", "activa")
    list_filter = ("negocio", "activa")
    search_fields = ("nombre",)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "nit", "negocio", "ciudad", "telefono", "activo")
    list_filter = ("negocio", "activo", "ciudad")
    search_fields = ("razon_social", "nit", "nombre_contacto")


class OfertaDeProveedorInline(admin.TabularInline):
    """Los proveedores de un producto se editan desde el propio producto."""

    model = ProductoProveedor
    extra = 1
    fields = ("proveedor", "precio_compra", "codigo_proveedor", "es_principal", "negocio")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "nombre",
        "categoria",
        "negocio",
        "costo",
        "precio_evento",
        "precio_mayorista",
        "activo",
    )
    list_filter = ("negocio", "categoria", "activo")
    search_fields = ("sku", "nombre")
    inlines = [OfertaDeProveedorInline]

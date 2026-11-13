from django.contrib import admin

from .models import Categoria, Producto, Proveedor


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


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "nombre",
        "categoria",
        "negocio",
        "costo",
        "precio_venta",
        "activo",
    )
    list_filter = ("negocio", "categoria", "activo")
    search_fields = ("sku", "nombre")

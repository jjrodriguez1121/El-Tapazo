"""Rutas HTTP de la app `catalogo`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/catalogo/.
Las vistas viven en `catalogo/api/`.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from catalogo.api import vistas

app_name = "catalogo"

router = SimpleRouter()
router.register("categorias", vistas.CategoriaViewSet, basename="categoria")
router.register("proveedores", vistas.ProveedorViewSet, basename="proveedor")
router.register("productos", vistas.ProductoViewSet, basename="producto")

urlpatterns = [path("", include(router.urls))]

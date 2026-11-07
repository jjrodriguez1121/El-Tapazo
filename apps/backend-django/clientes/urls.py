"""Rutas HTTP de la app `clientes`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/clientes/.
Las vistas viven en `clientes/api/`.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from clientes.api import vistas

app_name = "clientes"

router = SimpleRouter()
router.register("", vistas.ClienteViewSet, basename="cliente")

urlpatterns = [path("", include(router.urls))]

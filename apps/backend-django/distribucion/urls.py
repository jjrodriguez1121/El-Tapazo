"""Rutas HTTP de la app `distribucion`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/distribucion/.
Las vistas viven en `distribucion/api/`.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from distribucion.api import vistas

app_name = "distribucion"

router = SimpleRouter()
router.register("clientes", vistas.ClienteDistribucionViewSet, basename="cliente")
router.register("pedidos", vistas.PedidoDistribucionViewSet, basename="pedido")

urlpatterns = [path("", include(router.urls))]

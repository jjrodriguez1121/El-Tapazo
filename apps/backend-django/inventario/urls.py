"""Rutas HTTP de la app `inventario`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/inventario/.
Las vistas viven en `inventario/api/`.

La ruta fija de `valorizacion/` va **antes** del router para que no se lea como
el detalle de un recurso.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from inventario.api import vistas

app_name = "inventario"

router = SimpleRouter()
router.register("ubicaciones", vistas.UbicacionViewSet, basename="ubicacion")
router.register("existencias", vistas.ExistenciaViewSet, basename="existencia")
router.register("movimientos", vistas.MovimientoViewSet, basename="movimiento")

urlpatterns = [
    path("valorizacion/", vistas.ValorizacionView.as_view(), name="valorizacion"),
    path("", include(router.urls)),
]

"""Rutas HTTP de la app `negocios`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/negocios/.
Las vistas viven en `negocios/api/`.

Las rutas fijas van **antes** del router: si fueran después, `mio/` intentaría
leerse como el detalle de un negocio con id "mio".
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from negocios.api import vistas

app_name = "negocios"

router = SimpleRouter()
router.register("", vistas.NegocioViewSet, basename="negocio")

urlpatterns = [
    path("mio/", vistas.MiNegocioView.as_view(), name="mi-negocio"),
    path("informes/ventas/", vistas.ResumenDeVentasView.as_view(), name="resumen-de-ventas"),
    path("", include(router.urls)),
]

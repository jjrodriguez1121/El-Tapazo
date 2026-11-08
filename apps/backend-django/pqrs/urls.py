"""Rutas HTTP de PQR."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from pqrs.api import vistas

app_name = "pqrs"

router = SimpleRouter()
router.register("", vistas.PqrViewSet, basename="pqr")

urlpatterns = [path("", include(router.urls))]

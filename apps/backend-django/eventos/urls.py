"""Rutas HTTP de la app `eventos`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/eventos/.
Las vistas viven en `eventos/api/`.

La ruta del punto de control va **antes** del router: la llama un aparato con
su propio token, no una persona con sesión.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from eventos.api import vistas

app_name = "eventos"

router = SimpleRouter()
router.register("jornadas", vistas.JornadaViewSet, basename="jornada")
router.register("grupos", vistas.GrupoViewSet, basename="grupo")
router.register("cuentas", vistas.CuentaViewSet, basename="cuenta")
router.register("pedidos", vistas.PedidoViewSet, basename="pedido")
router.register("pulseras", vistas.PulseraViewSet, basename="pulsera")
router.register("dispositivos", vistas.DispositivoViewSet, basename="dispositivo")
router.register("alertas", vistas.AlertaViewSet, basename="alerta")

urlpatterns = [
    path(
        "puntos-de-control/consultar/",
        vistas.PuntoDeControlView.as_view(),
        name="punto-de-control",
    ),
    path("", include(router.urls)),
]

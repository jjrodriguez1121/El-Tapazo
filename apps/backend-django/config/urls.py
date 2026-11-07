"""Mapa de URLs del proyecto.

Cada app de dominio expone sus rutas en /api/v1/<app>/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path("negocios/", include("negocios.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("clientes/", include("clientes.urls")),
    path("catalogo/", include("catalogo.urls")),
    path("inventario/", include("inventario.urls")),
    path("eventos/", include("eventos.urls")),
    path("distribucion/", include("distribucion.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

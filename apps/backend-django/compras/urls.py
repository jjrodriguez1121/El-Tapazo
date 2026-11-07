from django.urls import path

from compras.api import vistas

app_name = "compras"

urlpatterns = [
    path("", vistas.compras),
    path("cuentas-por-pagar/", vistas.cuentas_por_pagar),
    path("<int:compra_id>/", vistas.compra_detalle),
]

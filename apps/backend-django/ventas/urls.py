from django.urls import path

from ventas.api import vistas

app_name = "ventas"

urlpatterns = [
    path("cuentas-por-cobrar/", vistas.cuentas_por_cobrar),
]

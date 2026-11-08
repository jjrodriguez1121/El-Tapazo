from django.urls import path

from ventas.api import vistas

app_name = "ventas"

urlpatterns = [
    path("", vistas.ventas),
    path("metodos-pago/", vistas.metodos_pago),
    path("cuentas-por-cobrar/", vistas.cuentas_por_cobrar),
    path("cuentas-por-cobrar/<int:cuenta_id>/", vistas.cuenta_por_cobrar_detalle),
    path("cuentas-por-cobrar/<int:cuenta_id>/abonos/", vistas.registrar_abono),
    path("<int:venta_id>/", vistas.venta_detalle),
]

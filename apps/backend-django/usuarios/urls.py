"""Rutas HTTP de la app `usuarios`.

Se incluye desde `config/urls.py` bajo el prefijo /api/v1/usuarios/.
Las vistas viven en `usuarios/api/`.

Las rutas fijas de `invitaciones/` van **antes** del router: si fueran
después, `invitaciones/pendiente/` intentaría leerse como el detalle de una
invitación con id "pendiente".
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from usuarios.api import vistas

app_name = "usuarios"

router = SimpleRouter()
router.register("invitaciones", vistas.InvitacionViewSet, basename="invitacion")

urlpatterns = [
    # Sesión
    path("sesiones/", vistas.InicioDeSesionView.as_view(), name="inicio-de-sesion"),
    path(
        "sesiones/renovacion/",
        vistas.RenovacionDeSesionView.as_view(),
        name="renovacion-de-sesion",
    ),
    path("sesiones/cierre/", vistas.CierreDeSesionView.as_view(), name="cierre-de-sesion"),
    path("yo/", vistas.UsuarioAutenticadoView.as_view(), name="usuario-autenticado"),
    # Contraseña
    path(
        "contrasena/recuperacion/",
        vistas.SolicitudDeRecuperacionView.as_view(),
        name="recuperacion-de-contrasena",
    ),
    path(
        "contrasena/restablecimiento/",
        vistas.NuevaContrasenaView.as_view(),
        name="restablecimiento-de-contrasena",
    ),
    path(
        "contrasena/cambio/",
        vistas.CambioDeContrasenaView.as_view(),
        name="cambio-de-contrasena",
    ),
    # Verificación de correo
    path(
        "verificacion-correo/solicitud/",
        vistas.SolicitudDeVerificacionView.as_view(),
        name="solicitud-de-verificacion",
    ),
    path(
        "verificacion-correo/confirmacion/",
        vistas.ConfirmacionDeVerificacionView.as_view(),
        name="confirmacion-de-verificacion",
    ),
    # Invitaciones abiertas al público (quien recibió el correo)
    path(
        "invitaciones/pendiente/",
        vistas.InvitacionPendienteView.as_view(),
        name="invitacion-pendiente",
    ),
    path(
        "invitaciones/aceptacion/",
        vistas.AceptacionDeInvitacionView.as_view(),
        name="aceptacion-de-invitacion",
    ),
    path("", include(router.urls)),
]

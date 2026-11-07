"""Los correos que manda el módulo de identidad.

Se envían con `transaction.on_commit` desde los servicios que escriben: así no
sale un correo diciendo "te invitaron" si la transacción termina deshaciéndose.

Un fallo del proveedor **no tumba la operación**. Si el servidor de correo está
caído, la invitación ya quedó creada y el administrador puede reenviarla; que
la petición devolviera 500 solo haría que el trabajo se perdiera. El error
queda en los logs con su traza.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from usuarios.models import Invitacion, Usuario

logger = logging.getLogger(__name__)

# Rutas del frontend, no del backend: estas pantallas las pinta React.
RUTA_INVITACION = "/invitacion"
RUTA_NUEVA_CONTRASENA = "/nueva-contrasena"
RUTA_VERIFICAR_CORREO = "/verificar-correo"


def enviar_invitacion(*, invitacion: Invitacion, token: str) -> None:
    """Le manda al invitado el enlace con el que creará su contraseña."""
    _enviar(
        asunto=f"Te invitaron a {invitacion.negocio.nombre_comercial} en El Tapaso",
        plantilla="correos/invitacion.txt",
        destinatario=invitacion.correo,
        contexto={
            "negocio": invitacion.negocio.nombre_comercial,
            "rol": invitacion.get_rol_display(),
            "invitada_por": invitacion.creada_por.nombre_completo,
            "expira_en": invitacion.expira_en,
            "enlace": _enlace(RUTA_INVITACION, token=token),
        },
    )


def enviar_recuperacion_de_contrasena(*, usuario: Usuario, uid: str, token: str) -> None:
    """Le manda el enlace para elegir una contraseña nueva."""
    _enviar(
        asunto="Recupera tu contraseña de El Tapaso",
        plantilla="correos/recuperacion_contrasena.txt",
        destinatario=usuario.correo,
        contexto={
            "nombre": usuario.nombre,
            "horas_de_vigencia": _horas_de_vigencia(),
            "enlace": _enlace(RUTA_NUEVA_CONTRASENA, uid=uid, token=token),
        },
    )


def enviar_verificacion_de_correo(*, usuario: Usuario, uid: str, token: str) -> None:
    """Le manda el enlace que confirma que el correo es suyo."""
    _enviar(
        asunto="Verifica tu correo de El Tapaso",
        plantilla="correos/verificacion_correo.txt",
        destinatario=usuario.correo,
        contexto={
            "nombre": usuario.nombre,
            "horas_de_vigencia": _horas_de_vigencia(),
            "enlace": _enlace(RUTA_VERIFICAR_CORREO, uid=uid, token=token),
        },
    )


def _enviar(*, asunto: str, plantilla: str, destinatario: str, contexto: dict) -> None:
    cuerpo = render_to_string(plantilla, contexto)
    try:
        send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario])
    except OSError:
        # `OSError` cubre lo que puede fallar aquí: `SMTPException` hereda de
        # ella, igual que los errores de red al abrir la conexión.
        logger.exception("No se pudo enviar el correo «%s»", asunto)


def _enlace(ruta: str, **parametros: str) -> str:
    """Arma la URL del frontend. El token nunca se escribe en los logs."""
    return f"{settings.URL_FRONTEND.rstrip('/')}{ruta}?{urlencode(parametros)}"


def _horas_de_vigencia() -> int:
    return settings.PASSWORD_RESET_TIMEOUT // 3600

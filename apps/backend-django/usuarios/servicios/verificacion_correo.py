"""Verificación del correo: el paso que falta para poder entrar."""

import logging

from django.utils import timezone

from usuarios.models import Usuario
from usuarios.repositorios import usuarios as repositorio
from usuarios.servicios import correos
from usuarios.servicios.enlaces import usuario_del_enlace
from usuarios.tokens import codificar_id, token_de_verificacion

logger = logging.getLogger(__name__)


def solicitar_verificacion(*, correo: str) -> None:
    """Manda (o vuelve a mandar) el enlace de verificación.

    Como en la recuperación de contraseña, no lanza nada si el correo no
    existe o ya está verificado: el endpoint responde siempre lo mismo para no
    servir de directorio de quién tiene cuenta.
    """
    usuario = repositorio.obtener_por_correo(correo=correo)
    if usuario is None or not usuario.activo or usuario.correo_esta_verificado:
        logger.info("Verificación pedida para un correo que no la necesita.")
        return

    correos.enviar_verificacion_de_correo(
        usuario=usuario,
        uid=codificar_id(usuario.pk),
        token=token_de_verificacion.make_token(usuario),
    )


def confirmar_verificacion(*, uid: str, token: str) -> Usuario:
    """Marca el correo como verificado.

    El enlace sirve una sola vez: `correo_verificado_en` entra en la firma del
    token, así que al llenarse deja de cuadrar. Abrir dos veces el mismo
    enlace da `enlace_invalido`, no un error raro.

    Raises:
        EnlaceInvalido: enlace manipulado, vencido o ya usado.
    """
    usuario = usuario_del_enlace(uid=uid, token=token, generador=token_de_verificacion)
    usuario.correo_verificado_en = timezone.now()
    usuario.save(update_fields=["correo_verificado_en"])
    return usuario

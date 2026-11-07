"""Recuperar, restablecer y cambiar la contraseña."""

import logging

from django.db import transaction

from usuarios.dtos import SesionDTO
from usuarios.excepciones import ContrasenaActualIncorrecta
from usuarios.models import Usuario
from usuarios.repositorios import usuarios as repositorio
from usuarios.servicios import correos, sesiones
from usuarios.servicios.enlaces import usuario_del_enlace
from usuarios.tokens import codificar_id, token_de_recuperacion
from usuarios.validadores.contrasenas import validar_contrasena

logger = logging.getLogger(__name__)


def solicitar_recuperacion(*, correo: str) -> None:
    """Manda el enlace de recuperación, si hay a quién mandárselo.

    No lanza nada cuando el correo no existe, y el endpoint responde siempre
    lo mismo: si contestara distinto, cualquiera podría averiguar qué correos
    tienen cuenta escribiéndolos uno por uno en "olvidé mi contraseña".
    """
    usuario = repositorio.obtener_por_correo(correo=correo)
    if usuario is None or not usuario.activo:
        logger.info("Recuperación pedida para un correo sin cuenta activa.")
        return

    correos.enviar_recuperacion_de_contrasena(
        usuario=usuario,
        uid=codificar_id(usuario.pk),
        token=token_de_recuperacion.make_token(usuario),
    )


@transaction.atomic
def restablecer_contrasena(*, uid: str, token: str, contrasena_nueva: str) -> None:
    """Cambia la contraseña desde el enlace del correo.

    Raises:
        EnlaceInvalido: el enlace no es legítimo o ya venció.
        ContrasenaInsegura: la contraseña nueva no pasa los validadores.
    """
    usuario = usuario_del_enlace(uid=uid, token=token, generador=token_de_recuperacion)
    _guardar_contrasena(usuario=usuario, contrasena_nueva=contrasena_nueva)


@transaction.atomic
def cambiar_contrasena(
    *, usuario: Usuario, contrasena_actual: str, contrasena_nueva: str
) -> SesionDTO:
    """Cambia la contraseña de quien ya está dentro.

    Devuelve una sesión nueva porque el cambio cierra todas las anteriores,
    incluida la que se está usando: sin esto, quien acaba de cambiar su
    contraseña se quedaría en la calle en la siguiente petición.

    Raises:
        ContrasenaActualIncorrecta: no acertó la que tiene ahora.
        ContrasenaInsegura: la nueva no pasa los validadores.
    """
    if not usuario.check_password(contrasena_actual):
        raise ContrasenaActualIncorrecta

    _guardar_contrasena(usuario=usuario, contrasena_nueva=contrasena_nueva)
    return sesiones.abrir_sesion(usuario=usuario)


def _guardar_contrasena(*, usuario: Usuario, contrasena_nueva: str) -> None:
    """Valida, guarda y deja fuera a todas las sesiones abiertas.

    Cerrarlas es la mitad del sentido de cambiar una contraseña: si el motivo
    era que alguien más la sabía, dejarle la sesión abierta no arregla nada.
    """
    validar_contrasena(contrasena=contrasena_nueva, usuario=usuario)
    usuario.set_password(contrasena_nueva)
    usuario.save(update_fields=["password"])
    sesiones.cerrar_todas_las_sesiones(usuario_id=usuario.pk)

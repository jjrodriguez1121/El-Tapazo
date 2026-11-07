"""Abrir, renovar y cerrar sesión."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.dtos import SesionDTO
from usuarios.excepciones import (
    CorreoNoVerificado,
    CredencialesInvalidas,
    NegocioSuspendido,
    SesionInvalida,
    UsuarioInactivo,
)
from usuarios.models import Usuario


def iniciar_sesion(*, correo: str, contrasena: str) -> SesionDTO:
    """Comprueba las credenciales y entrega el par de tokens.

    Raises:
        CredencialesInvalidas: el correo no existe o la contraseña no es esa.
        UsuarioInactivo, CorreoNoVerificado, NegocioSuspendido: la contraseña
            era correcta, pero la cuenta todavía no puede operar.
    """
    usuario = authenticate(correo=correo.strip().lower(), password=contrasena)
    if usuario is None:
        raise CredencialesInvalidas
    _comprobar_que_la_cuenta_puede_operar(usuario)
    update_last_login(None, usuario)
    return abrir_sesion(usuario=usuario)


def renovar_sesion(*, token_de_refresco: str) -> tuple[str, str]:
    """Entrega un acceso nuevo y rota el refresco.

    El refresco entregado antes queda anulado: si alguien copió uno, deja de
    servir en cuanto la persona legítima renueva.

    Returns:
        La pareja (acceso, refresco) nueva.
    """
    try:
        refresco = RefreshToken(token_de_refresco)
        acceso = str(refresco.access_token)
        refresco.blacklist()
    except TokenError as exc:
        raise SesionInvalida from exc

    refresco.set_jti()
    refresco.set_exp()
    refresco.set_iat()
    return acceso, str(refresco)


def cerrar_sesion(*, token_de_refresco: str) -> None:
    """Anula el refresco para que no sirva más.

    En un bar los dispositivos se comparten: cerrar sesión tiene que invalidar
    de verdad, no solo borrar el token del navegador.

    Si el token ya no valía, no se avisa de nada: el objetivo —que no sirva—
    ya está cumplido, y hacer fallar un cierre de sesión solo deja al usuario
    atrapado en una pantalla de la que quería salir.
    """
    try:
        RefreshToken(token_de_refresco).blacklist()
    except TokenError:
        return


def cerrar_todas_las_sesiones(*, usuario_id: int) -> None:
    """Anula todos los refrescos de una persona.

    Se llama al cambiar la contraseña: si alguien había entrado con la vieja,
    se queda fuera. Los accesos ya emitidos siguen valiendo hasta que caduquen
    —son minutos—, que es el precio de que la API no consulte la base de datos
    en cada petición.
    """
    for token in OutstandingToken.objects.filter(user_id=usuario_id):
        BlacklistedToken.objects.get_or_create(token=token)


def _comprobar_que_la_cuenta_puede_operar(usuario: Usuario) -> None:
    """Las tres razones por las que una contraseña correcta no basta.

    Se comprueban **después** de la contraseña, y no antes, a propósito: así
    la API solo cuenta el estado de una cuenta a quien ya demostró que es
    suya. De lo contrario el formulario de acceso serviría para averiguar qué
    correos están registrados.
    """
    if not usuario.activo:
        raise UsuarioInactivo
    if not usuario.correo_esta_verificado:
        raise CorreoNoVerificado
    # El staff de la plataforma no tiene negocio: no hay negocio que revisar.
    if usuario.negocio is not None and not usuario.negocio.esta_operativo:
        raise NegocioSuspendido


def abrir_sesion(*, usuario: Usuario) -> SesionDTO:
    """Entrega el par de tokens de una cuenta ya comprobada.

    La comprobación es de quien llama: esta función solo firma.
    """
    refresco = RefreshToken.for_user(usuario)
    return SesionDTO(
        usuario=usuario,
        token_de_acceso=str(refresco.access_token),
        token_de_refresco=str(refresco),
    )

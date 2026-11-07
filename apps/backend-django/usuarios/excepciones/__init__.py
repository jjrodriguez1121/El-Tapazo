"""Errores propios del dominio de identidad y acceso."""

from usuarios.excepciones.contrasenas import ContrasenaActualIncorrecta, ContrasenaInsegura
from usuarios.excepciones.enlaces import EnlaceInvalido
from usuarios.excepciones.invitaciones import (
    CorreoYaRegistrado,
    InvitacionNoEncontrada,
    InvitacionVencida,
    InvitacionYaAceptada,
    YaHayInvitacionPendiente,
)
from usuarios.excepciones.sesiones import (
    CorreoNoVerificado,
    CredencialesInvalidas,
    NegocioSuspendido,
    SesionInvalida,
    UsuarioInactivo,
)

__all__ = [
    "ContrasenaActualIncorrecta",
    "ContrasenaInsegura",
    "CorreoNoVerificado",
    "CorreoYaRegistrado",
    "CredencialesInvalidas",
    "EnlaceInvalido",
    "InvitacionNoEncontrada",
    "InvitacionVencida",
    "InvitacionYaAceptada",
    "NegocioSuspendido",
    "SesionInvalida",
    "UsuarioInactivo",
    "YaHayInvitacionPendiente",
]

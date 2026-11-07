"""Errores del alta de trabajadores por invitación."""

from nucleo.excepciones import ErrorDeNegocio


class InvitacionNoEncontrada(ErrorDeNegocio):
    mensaje = "Esa invitación no existe."
    codigo = "invitacion_no_encontrada"
    status_http = 404


class InvitacionVencida(ErrorDeNegocio):
    mensaje = "La invitación venció. Pídele al administrador que te envíe otra."
    codigo = "invitacion_vencida"
    status_http = 409


class InvitacionYaAceptada(ErrorDeNegocio):
    mensaje = "Esa invitación ya se usó. Inicia sesión con tu correo."
    codigo = "invitacion_ya_aceptada"
    status_http = 409


class YaHayInvitacionPendiente(ErrorDeNegocio):
    """Lo mismo que impide la restricción parcial de la base de datos."""

    mensaje = "Ya hay una invitación pendiente para ese correo."
    codigo = "invitacion_pendiente_duplicada"
    status_http = 409


class CorreoYaRegistrado(ErrorDeNegocio):
    mensaje = "Ya existe un usuario con ese correo."
    codigo = "correo_ya_registrado"
    status_http = 409

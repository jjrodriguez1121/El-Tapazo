"""Errores al intentar entrar al sistema."""

from nucleo.excepciones import ErrorDeNegocio


class CredencialesInvalidas(ErrorDeNegocio):
    """Correo que no existe, o contraseña equivocada.

    El mensaje es el mismo en los dos casos a propósito: si dijera "ese correo
    no existe", el formulario de acceso se convertiría en una forma cómoda de
    averiguar quién trabaja en el negocio.
    """

    mensaje = "El correo o la contraseña no son correctos."
    codigo = "credenciales_invalidas"
    status_http = 401


class UsuarioInactivo(ErrorDeNegocio):
    mensaje = "Esta cuenta está desactivada. Habla con el administrador de tu negocio."
    codigo = "usuario_inactivo"
    status_http = 403


class CorreoNoVerificado(ErrorDeNegocio):
    """La contraseña era correcta, pero falta abrir el enlace del correo."""

    mensaje = "Tienes que verificar tu correo antes de entrar. Te enviamos un enlace."
    codigo = "correo_no_verificado"
    status_http = 403


class NegocioSuspendido(ErrorDeNegocio):
    mensaje = "El negocio está suspendido. Nadie puede operar mientras siga así."
    codigo = "negocio_suspendido"
    status_http = 403


class SesionInvalida(ErrorDeNegocio):
    """El token de refresco no vale: caducado, manipulado o ya usado."""

    mensaje = "Tu sesión expiró. Vuelve a iniciar sesión."
    codigo = "sesion_invalida"
    status_http = 401

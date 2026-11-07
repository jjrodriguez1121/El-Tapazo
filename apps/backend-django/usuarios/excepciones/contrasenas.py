"""Errores al elegir o cambiar una contraseña."""

from nucleo.excepciones import ErrorDeNegocio


class ContrasenaInsegura(ErrorDeNegocio):
    """No pasó los validadores de Django (corta, sin letras o sin números).

    Los motivos concretos van en `detalles`, para que el formulario los pinte
    todos de una vez en vez de uno por intento.
    """

    mensaje = "La contraseña no cumple los requisitos mínimos."
    codigo = "contrasena_insegura"
    status_http = 400


class ContrasenaActualIncorrecta(ErrorDeNegocio):
    mensaje = "La contraseña actual no es correcta."
    codigo = "contrasena_actual_incorrecta"
    status_http = 400

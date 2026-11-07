"""Errores de los enlaces que se mandan por correo."""

from nucleo.excepciones import ErrorDeNegocio


class EnlaceInvalido(ErrorDeNegocio):
    """Sirve para recuperación y para verificación.

    No se distingue "caducado" de "ya usado" ni de "inventado": los tres se
    arreglan igual —pidiendo otro enlace— y separarlos solo le diría a quien
    prueba tokens al azar cuánto se acercó.
    """

    mensaje = "El enlace no es válido o ya venció. Solicita uno nuevo."
    codigo = "enlace_invalido"
    status_http = 400

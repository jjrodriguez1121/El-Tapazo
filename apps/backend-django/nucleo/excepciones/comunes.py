"""Errores que se repetirían igual en todas las apps."""

from nucleo.excepciones.base import ErrorDeNegocio


class NoEncontradoEnEsteNegocio(ErrorDeNegocio):
    """Lo que se pidió no existe, o existe pero es de otro negocio.

    Los dos casos responden lo mismo **a propósito**: contestar `403` cuando
    el recurso existe pero es ajeno ya sería contar de más — confirmaría que
    ese id existe en la plataforma. Con `404` los dos casos son
    indistinguibles desde fuera.

    Por lo mismo comparte el `codigo` del 404 genérico: el frontend no tiene
    que distinguirlos, y no debería poder.
    """

    mensaje = "No se encontró lo que buscas."
    codigo = "no_encontrado"
    status_http = 404

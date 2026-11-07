"""Errores propios de las fichas de cliente."""

from nucleo.excepciones import ErrorDeNegocio


class DocumentoDuplicado(ErrorDeNegocio):
    """Ya hay una ficha con ese documento en el negocio.

    Es la regla que hace que quien vuelve el sábado siguiente sea la misma
    ficha con su historial, en vez de "Juan", "Juan P" y "Juan Perez".
    """

    mensaje = "Ya hay un cliente con ese documento en este negocio."
    codigo = "documento_duplicado"
    status_http = 409


class FechaDeNacimientoInvalida(ErrorDeNegocio):
    """La fecha no es una fecha de nacimiento posible.

    No comprueba la mayoría de edad: eso **no bloquea nada** (decisión 7), y
    además cambia sola con el tiempo. Esto solo descarta lo imposible.
    """

    mensaje = "La fecha de nacimiento no es válida."
    codigo = "fecha_de_nacimiento_invalida"
    status_http = 400

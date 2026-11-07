"""Errores propios de la administración de negocios."""

from nucleo.excepciones import ErrorDeNegocio


class NegocioNoEncontrado(ErrorDeNegocio):
    """No hay ningún negocio con ese id.

    No usa `NoEncontradoEnEsteNegocio` de `nucleo` porque aquí **no hay
    aislamiento que proteger**: quien pregunta es el staff de la plataforma y
    los ve todos. El `codigo` sí es el mismo del 404 genérico — el frontend no
    tiene que distinguir un 404 de otro.
    """

    mensaje = "No se encontró ese negocio."
    codigo = "no_encontrado"
    status_http = 404


class NitDeNegocioDuplicado(ErrorDeNegocio):
    """Ya hay un negocio con ese NIT.

    El NIT es único **global** y no por negocio, al revés que casi todo lo
    demás: aquí el negocio es la fila, no el dueño de la fila. Dos negocios con
    el mismo NIT serían el mismo negocio dado de alta dos veces.
    """

    mensaje = "Ya hay un negocio con ese NIT en la plataforma."
    codigo = "nit_de_negocio_duplicado"
    status_http = 409


class NegocioYaSuspendido(ErrorDeNegocio):
    """Suspender lo que ya está suspendido no cambia nada.

    Se responde con un error y no en silencio para que quien administra sepa
    que lo que creía que iba a hacer ya estaba hecho.
    """

    mensaje = "Ese negocio ya está suspendido."
    codigo = "negocio_ya_suspendido"
    status_http = 409


class NegocioYaActivo(ErrorDeNegocio):
    """Reactivar lo que nunca se suspendió no cambia nada."""

    mensaje = "Ese negocio ya está activo."
    codigo = "negocio_ya_activo"
    status_http = 409


class RangoDeFechasInvalido(ErrorDeNegocio):
    """El informe empieza después de acabar."""

    mensaje = "La fecha de inicio no puede ser posterior a la del final."
    codigo = "rango_de_fechas_invalido"
    status_http = 400

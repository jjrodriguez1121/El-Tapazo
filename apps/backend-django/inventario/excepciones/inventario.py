"""Errores propios del inventario.

Los "no encontrado" no están aquí: para eso está `NoEncontradoEnEsteNegocio`
de `nucleo`, que responde igual tanto si la fila no existe como si es de otro
negocio.
"""

from nucleo.excepciones import ErrorDeNegocio


class ExistenciasInsuficientes(ErrorDeNegocio):
    """No hay tanto de ese producto en esa ubicación.

    Los `detalles` llevan el producto, lo solicitado y lo disponible: es lo que
    deja a la pantalla decir «quedan 3» en vez de «no se pudo».
    """

    mensaje = "No hay existencias suficientes para completar la operación."
    codigo = "existencias_insuficientes"
    status_http = 409


class MovimientoYaAnulado(ErrorDeNegocio):
    """Ese movimiento ya tiene su contrario. Anularlo otra vez lo duplicaría."""

    mensaje = "Ese movimiento ya fue anulado."
    codigo = "movimiento_ya_anulado"
    status_http = 409


class CantidadInvalida(ErrorDeNegocio):
    """La cantidad no tiene sentido: cero, del signo contrario o imposible."""

    mensaje = "La cantidad no es válida para esta operación."
    codigo = "cantidad_invalida"
    status_http = 400


class MotivoObligatorio(ErrorDeNegocio):
    """Un ajuste o una anulación sin motivo no sirve para nada.

    Ésta es la tabla donde se detecta un faltante: un ajuste que no dice por
    qué se hizo es exactamente lo que no puede pasar.
    """

    mensaje = "Hay que decir por qué se hace este movimiento."
    codigo = "motivo_obligatorio"
    status_http = 400

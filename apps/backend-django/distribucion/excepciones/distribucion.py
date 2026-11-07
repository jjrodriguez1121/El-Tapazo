"""Errores propios del canal mayorista.

Los "no encontrado" no están aquí: para eso está `NoEncontradoEnEsteNegocio`
de `nucleo`, que responde igual tanto si la fila no existe como si es de otro
negocio. Distinguirlas ya sería contar de más.
"""

from nucleo.excepciones import ErrorDeNegocio


class NitDuplicado(ErrorDeNegocio):
    """Ya hay una tienda con ese NIT en el negocio.

    Es la regla que hace que la tienda que vuelve a pedir el mes siguiente sea
    la misma ficha con su historial de crédito, y no una segunda "La Esquina".
    """

    mensaje = "Ya hay un cliente con ese NIT en este negocio."
    codigo = "nit_duplicado"
    status_http = 409


class PedidoSinLineas(ErrorDeNegocio):
    """Un pedido sin nada que despachar no es un pedido."""

    mensaje = "El pedido no tiene productos."
    codigo = "pedido_sin_lineas"
    status_http = 400


class PedidoNoDespachable(ErrorDeNegocio):
    """Solo sale al camión lo que está en la bodega.

    Se despacha desde `pendiente` —nunca salió— y desde `no_entregado` —volvió
    (decisión 5). Desde `en_ruta` ya está fuera, y desde `entregado` o
    `cancelado` no hay nada que cargar.
    """

    mensaje = "Ese pedido no se puede despachar en su estado actual."
    codigo = "pedido_no_despachable"
    status_http = 409


class PedidoNoEntregable(ErrorDeNegocio):
    """Solo se entrega lo que va en el camión: `en_ruta`."""

    mensaje = "Ese pedido no está en ruta, así que no se puede entregar."
    codigo = "pedido_no_entregable"
    status_http = 409


class PedidoNoCancelable(ErrorDeNegocio):
    """Cancelar solo se permite con la mercancía en la bodega.

    Desde `en_ruta` se rechaza pidiendo marcar primero `no_entregado`: el
    atajo dejaría el saldo descontado para siempre, sin ninguna fila del kardex
    que explicara el regreso. Desde `entregado` tampoco — eso es una
    devolución, y es otra operación.
    """

    mensaje = "Ese pedido ya no se puede cancelar."
    codigo = "pedido_no_cancelable"
    status_http = 409


class MotivoObligatorio(ErrorDeNegocio):
    """Un pedido que volvió sin entregarse y no dice por qué no sirve para nada.

    No se puede llamar a la tienda ni corregir la ruta. La base lo garantiza
    además con `pedido_distribucion_no_entregado_con_motivo`; esto solo lo dice
    antes y con un mensaje que se entiende.
    """

    mensaje = "Hay que decir por qué no se pudo entregar."
    codigo = "motivo_obligatorio"
    status_http = 400


class PagoSuperaElTotal(ErrorDeNegocio):
    """Los abonos de un pedido no pueden pasar de lo que vale.

    Es la única regla de este canal que **no está declarada en la base**: "la
    suma de los pagos no supera el total" es un agregado, y una restricción de
    fila no puede mirar las otras filas. La comprueba el servicio, bloqueando
    el pedido antes de sumar. Es una limitación de SQL, no una decisión de
    diseño.
    """

    mensaje = "El abono pasa de lo que falta por pagar."
    codigo = "pago_supera_el_total"
    status_http = 409


class PedidoNoCobrable(ErrorDeNegocio):
    """Un pedido cancelado no admite abonos: no hay nada que cobrar."""

    mensaje = "Ese pedido está cancelado: no admite abonos."
    codigo = "pedido_no_cobrable"
    status_http = 409

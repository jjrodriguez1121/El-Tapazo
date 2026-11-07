"""Errores propios del canal evento/bar.

Los "no encontrado" no están aquí: para eso está `NoEncontradoEnEsteNegocio`
de `nucleo`.
"""

from nucleo.excepciones import ErrorDeNegocio


class EventoSinUbicacion(ErrorDeNegocio):
    """No se puede vender en un evento que todavía no sabe dónde se monta.

    No hay de dónde descontar la mercancía. Es un caso que la apertura
    automática nunca produce, porque abre la jornada *de* una ubicación: pasa
    solo con un evento planeado a mano al que no se le puso sitio.
    """

    mensaje = "Ese evento no tiene ubicación, así que no hay de dónde descontar."
    codigo = "evento_sin_ubicacion"
    status_http = 409


class JornadaNoAbierta(ErrorDeNegocio):
    """La jornada está planeada, cerrada o cancelada: no admite ventas."""

    mensaje = "Esa jornada no está abierta."
    codigo = "jornada_no_abierta"
    status_http = 409


class CuentasSinSaldar(ErrorDeNegocio):
    """Quedan cuentas abiertas: cerrar la caja las dejaría sin cobrar.

    Los `detalles` llevan la lista, para que la pantalla diga cuáles en vez de
    obligar a buscarlas una por una.
    """

    mensaje = "Quedan cuentas sin saldar. No se puede cerrar la caja."
    codigo = "cuentas_sin_saldar"
    status_http = 409


class GrupoCerrado(ErrorDeNegocio):
    """El grupo ya se cerró: no admite cuentas ni pedidos nuevos."""

    mensaje = "Ese grupo ya está cerrado."
    codigo = "grupo_cerrado"
    status_http = 409


class CuentaYaLiberada(ErrorDeNegocio):
    """La cuenta ya se cerró. Cobrarla otra vez cuadraría la caja de más."""

    mensaje = "Esa cuenta ya se cerró."
    codigo = "cuenta_ya_liberada"
    status_http = 409


class PulseraYaAsignada(ErrorDeNegocio):
    """Esa pulsera la lleva puesta otra persona ahora mismo.

    Lo garantiza la restricción `pulsera_con_una_sola_asignacion_activa`; esto
    solo lo traduce a un mensaje que se entiende.
    """

    mensaje = "Esa pulsera ya está asignada a una cuenta abierta."
    codigo = "pulsera_ya_asignada"
    status_http = 409


class PulseraNoDisponible(ErrorDeNegocio):
    """El chip está dañado, perdido o retirado: no se le puede poner a nadie."""

    mensaje = "Esa pulsera no está disponible."
    codigo = "pulsera_no_disponible"
    status_http = 409


class PagoNoCubreElConsumo(ErrorDeNegocio):
    """Una cuenta del bar se salda con un solo pago que cubre el total.

    Aquí no hay abonos, y es a propósito (decisión 3): los abonos son del canal
    mayorista, donde una tienda a 30 días paga en varias veces.
    """

    mensaje = "El pago no cubre lo consumido."
    codigo = "pago_no_cubre_el_consumo"
    status_http = 409


class PedidoNoCancelable(ErrorDeNegocio):
    """Ya se cobró, o ya estaba cancelado.

    Una comanda cobrada no se cancela: eso es una devolución de dinero y es
    otra operación (decisión 11).
    """

    mensaje = "Esa comanda ya no se puede cancelar."
    codigo = "pedido_no_cancelable"
    status_http = 409


class MotivoObligatorio(ErrorDeNegocio):
    """Cancelar una comanda sin decir por qué no sirve para nada.

    El motivo va a la nota de los movimientos contrarios, que es donde alguien
    lo va a buscar cuando pregunte por qué subió el saldo sin que entrara
    mercancía.
    """

    mensaje = "Hay que decir por qué se cancela."
    codigo = "motivo_obligatorio"
    status_http = 400


class PedidoSinLineas(ErrorDeNegocio):
    """Una comanda sin nada que servir no es una comanda."""

    mensaje = "La comanda no tiene productos."
    codigo = "pedido_sin_lineas"
    status_http = 400


class UidDuplicado(ErrorDeNegocio):
    """Ya hay una pulsera con ese UID en el negocio.

    El UID viene de fábrica y no se repite entre chips, así que si choca es que
    esa pulsera ya se dio de alta.
    """

    mensaje = "Ya hay una pulsera con ese UID en este negocio."
    codigo = "uid_duplicado"
    status_http = 409

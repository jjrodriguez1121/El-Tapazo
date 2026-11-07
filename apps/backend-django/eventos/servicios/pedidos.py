"""La venta: tomar una comanda, entregarla y cancelarla.

Una comanda descuenta el inventario **al crearse** (decisión 1), no al
entregarse: entre que el mesero la toma y la sirve, la cerveza ya está fuera de
la nevera. Sin existencias suficientes se bloquea siempre, sin excepción para
el administrador (decisión 2).
"""

from decimal import Decimal

from django.db import transaction

from catalogo.repositorios import productos as repositorio_de_productos
from eventos.dtos import LineaDePedidoDTO
from eventos.excepciones import (
    EventoSinUbicacion,
    JornadaNoAbierta,
    MotivoObligatorio,
    PedidoNoCancelable,
    PedidoSinLineas,
)
from eventos.models import DetallePedidoEvento, Evento, PedidoEvento
from eventos.repositorios import pedidos as repositorio
from eventos.servicios.alertas import revisar_limite_de_consumo
from eventos.servicios.cuentas import obtener_cuenta
from eventos.servicios.jornadas import obtener_jornada
from inventario.dtos import LineaDeProductoDTO
from inventario.models import MovimientoInventario
from inventario.servicios import consumo
from nucleo.excepciones import NoEncontradoEnEsteNegocio

REFERENCIA = MovimientoInventario.ReferenciaTipo.PEDIDO_EVENTO


@transaction.atomic
def registrar_pedido(
    *,
    evento_id: int,
    cliente_evento_id: int | None,
    lineas: list[LineaDePedidoDTO],
    mesero_id: int,
    negocio_id: int,
) -> PedidoEvento:
    """Toma una comanda y descuenta lo que lleva.

    `cliente_evento_id` vacío es la **venta de mostrador**: quien pide una
    cerveza, paga y se va. El inventario se descuenta igual; lo único que no se
    sabe es a quién se le vendió.

    **El orden importa, y es a propósito:** primero la cabecera (para tener el
    id que va a la referencia del kardex), luego los detalles, y el inventario
    **al final**. Todo lo caro —resolver productos, precios, la cuenta— pasa
    antes de tomar el primer bloqueo, para que los bloqueos sobre `existencias`
    duren lo mínimo. Con conexiones persistentes, una transacción larga con
    bloqueos abiertos es lo que tumba una barra en hora pico.

    Si falta stock no queda ni el pedido: la transacción lo deshace todo.

    Raises:
        PedidoSinLineas, NoEncontradoEnEsteNegocio, JornadaNoAbierta,
        EventoSinUbicacion, ExistenciasInsuficientes.
    """
    if not lineas:
        raise PedidoSinLineas

    jornada = obtener_jornada(evento_id=evento_id, negocio_id=negocio_id)
    if jornada.estado != Evento.Estado.EN_CURSO:
        raise JornadaNoAbierta
    if jornada.ubicacion_id is None:
        # La apertura automática nunca produce esto —abre la jornada *de* una
        # ubicación—, pero un evento planeado a mano puede quedarse sin sitio.
        raise EventoSinUbicacion

    if cliente_evento_id is not None:
        obtener_cuenta(cuenta_id=cliente_evento_id, negocio_id=negocio_id)

    precios = _precios_congelados(lineas=lineas, negocio_id=negocio_id)

    pedido = repositorio.crear(
        negocio_id=negocio_id,
        evento_id=evento_id,
        cliente_evento_id=cliente_evento_id,
        mesero_id=mesero_id,
    )
    repositorio.crear_detalles(
        detalles=[
            DetallePedidoEvento(
                negocio_id=negocio_id,
                pedido_evento_id=pedido.id,
                producto_id=linea.producto_id,
                cantidad=linea.cantidad,
                precio_unitario=precios[linea.producto_id],
            )
            for linea in lineas
        ]
    )

    consumo.descontar_por_venta(
        lineas=[
            LineaDeProductoDTO(producto_id=linea.producto_id, cantidad=linea.cantidad)
            for linea in lineas
        ],
        ubicacion_id=jornada.ubicacion_id,
        referencia_tipo=REFERENCIA,
        referencia_id=pedido.id,
        usuario_id=mesero_id,
        negocio_id=negocio_id,
    )

    if cliente_evento_id is not None:
        revisar_limite_de_consumo(cliente_evento_id=cliente_evento_id, negocio_id=negocio_id)
    return pedido


def entregar_pedido(*, pedido_id: int, negocio_id: int) -> PedidoEvento:
    """Marca la comanda como servida. **El stock ya salió** al tomarla.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoCancelable: ya está cancelada.
    """
    pedido = obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido.estado == PedidoEvento.Estado.CANCELADO:
        raise PedidoNoCancelable("Una comanda cancelada ya no se entrega.")

    pedido.estado = PedidoEvento.Estado.ENTREGADO
    pedido.save(update_fields=["estado", "actualizado_en"])
    return pedido


@transaction.atomic
def cancelar_pedido(
    *, pedido_id: int, negocio_id: int, usuario_id: int, motivo: str
) -> PedidoEvento:
    """Anula la comanda y devuelve al inventario **exactamente lo que descontó**.

    Se puede cancelar una comanda ya entregada mientras no esté cobrada
    (decisión 11): en una barra los errores se detectan después de servir. Una
    vez cobrada no, porque eso es una devolución de dinero y es otra operación.

    El motivo va a la nota de los movimientos contrarios, que es donde alguien
    lo va a buscar cuando pregunte por qué subió el saldo sin que entrara
    mercancía.

    Lo que se devuelve sale del **neto del kardex**, no de las líneas del
    pedido: es la misma puerta que usa el canal mayorista y la que hace que
    cancelar dos veces no reponga de más.

    Raises:
        NoEncontradoEnEsteNegocio, MotivoObligatorio, PedidoNoCancelable.
    """
    if not motivo or not motivo.strip():
        raise MotivoObligatorio

    pedido = obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido.estado == PedidoEvento.Estado.CANCELADO:
        raise PedidoNoCancelable("Esa comanda ya está cancelada.")
    if _ya_se_cobro(pedido=pedido, negocio_id=negocio_id):
        raise PedidoNoCancelable("Esa comanda ya se cobró. Devolver el dinero es otra operación.")

    consumo.devolver_lo_movido_por(
        referencia_tipo=REFERENCIA,
        referencia_id=pedido.id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=motivo.strip(),
    )
    pedido.estado = PedidoEvento.Estado.CANCELADO
    pedido.save(update_fields=["estado", "actualizado_en"])
    return pedido


def obtener_pedido(*, pedido_id: int, negocio_id: int) -> PedidoEvento:
    """Raises: NoEncontradoEnEsteNegocio."""
    pedido = repositorio.obtener_del_negocio(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido is None:
        raise NoEncontradoEnEsteNegocio
    return pedido


def _precios_congelados(*, lineas: list[LineaDePedidoDTO], negocio_id: int) -> dict[int, Decimal]:
    """El precio de venta **del momento**, leído del catálogo.

    No viaja en la petición a propósito: si lo mandara quien pide, cualquiera
    podría fijar el precio de su propia cerveza. Y se copia a la línea porque
    subir el precio mañana no puede cambiar los pedidos cerrados de ayer.

    Aquí se valida cada línea, **antes** de `bulk_create`, que no ejecuta las
    validaciones de Python: una cantidad en cero saldría como `IntegrityError`
    y llegaría al cliente como un 500.

    Raises:
        PedidoSinLineas: alguna cantidad no es positiva.
        NoEncontradoEnEsteNegocio: algún producto es de otro negocio.
    """
    if any(linea.cantidad <= 0 for linea in lineas):
        raise PedidoSinLineas("Las cantidades de la comanda deben ser mayores que cero.")

    ids = {linea.producto_id for linea in lineas}
    productos = repositorio_de_productos.del_negocio(negocio_id=negocio_id).filter(pk__in=ids)
    precios = {producto.id: producto.precio_evento for producto in productos}
    if len(precios) != len(ids):
        raise NoEncontradoEnEsteNegocio
    return precios


def _ya_se_cobro(*, pedido: PedidoEvento, negocio_id: int) -> bool:
    """Una venta de mostrador se cobra contra el pedido; una cuenta, al cerrarla."""
    if pedido.cliente_evento_id is None:
        return repositorio.tiene_pago(pedido_id=pedido.id, negocio_id=negocio_id)
    return pedido.cliente_evento.liberada_en is not None

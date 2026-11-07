"""El pedido mayorista: tomarlo, despacharlo, entregarlo y lo que sale mal.

El ciclo de un pedido y qué hace cada paso con el inventario:

```
pendiente ──despachar──► en_ruta ──entregar──► entregado
    ▲                       │
    │                  no entregar
    │                       ▼
    └───── despachar ── no_entregado ──► cancelado
```

**El stock sale al despachar y no al entregar** (decisión 4): entre las dos
cosas la mercancía va en el camión, o sea que ya no está en la bodega, y el
sistema tiene que decir lo mismo que dice el estante. Por lo mismo, cuando no
se pudo entregar la devolución es **inmediata** y no "cuando el camión llegue":
entre una cosa y otra el sistema estaría diciendo que hay menos cerveza de la
que hay, y el bar dejaría de vender por un faltante que no existe.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from catalogo.repositorios import productos as repositorio_de_productos
from distribucion.dtos import LineaDePedidoDTO
from distribucion.excepciones import (
    MotivoObligatorio,
    PedidoNoCancelable,
    PedidoNoDespachable,
    PedidoNoEntregable,
    PedidoSinLineas,
)
from distribucion.models import DetallePedidoDistribucion, PedidoDistribucion
from distribucion.repositorios import pedidos as repositorio
from distribucion.selectores import obtener_cliente, obtener_pedido
from inventario.dtos import LineaDeProductoDTO
from inventario.models import MovimientoInventario
from inventario.servicios import consumo
from nucleo.excepciones import NoEncontradoEnEsteNegocio

REFERENCIA = MovimientoInventario.ReferenciaTipo.PEDIDO_DISTRIBUCION


@transaction.atomic
def crear_pedido(
    *,
    cliente_distribucion_id: int,
    lineas: list[LineaDePedidoDTO],
    usuario_id: int,
    negocio_id: int,
) -> PedidoDistribucion:
    """Toma el pedido de una tienda y congela sus precios.

    **No toca el stock:** un pedido pendiente todavía no salió de la bodega.
    Eso pasa al despacharlo.

    Raises:
        PedidoSinLineas, NoEncontradoEnEsteNegocio.
    """
    if not lineas:
        raise PedidoSinLineas

    obtener_cliente(cliente_id=cliente_distribucion_id, negocio_id=negocio_id)
    precios = _precios_congelados(lineas=lineas, negocio_id=negocio_id)

    pedido = repositorio.crear(
        negocio_id=negocio_id,
        cliente_distribucion_id=cliente_distribucion_id,
        usuario_id=usuario_id,
    )
    repositorio.crear_detalles(
        detalles=[
            DetallePedidoDistribucion(
                negocio_id=negocio_id,
                pedido_distribucion_id=pedido.id,
                producto_id=linea.producto_id,
                cantidad=linea.cantidad,
                precio_unitario=precios[linea.producto_id],
            )
            for linea in lineas
        ]
    )
    return pedido


@transaction.atomic
def despachar_pedido(
    *, pedido_id: int, negocio_id: int, ubicacion_id: int, usuario_id: int
) -> PedidoDistribucion:
    """Carga el pedido en el camión y lo descuenta de esa bodega.

    La bodega se dice al despachar y no al tomar el pedido porque es entonces
    cuando se sabe: el pedido se toma por teléfono y se carga donde haya
    mercancía. Lo que salió de cada sitio queda en el kardex, que es lo que
    después sabe dónde devolverlo.

    Un pedido que volvió sin entregarse se vuelve a despachar por aquí mismo
    (decisión 5), y de paso se le limpia el motivo: ya no es cierto.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoDespachable, ExistenciasInsuficientes.
    """
    pedido = _bloquear(pedido_id=pedido_id, negocio_id=negocio_id)
    if not pedido.se_puede_despachar:
        raise PedidoNoDespachable(estado=pedido.estado)

    lineas = repositorio.detalles_de(pedido_id=pedido.id, negocio_id=negocio_id)
    consumo.descontar_por_venta(
        lineas=[
            LineaDeProductoDTO(producto_id=linea.producto_id, cantidad=linea.cantidad)
            for linea in lineas
        ],
        ubicacion_id=ubicacion_id,
        referencia_tipo=REFERENCIA,
        referencia_id=pedido.id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
    )

    pedido.estado = PedidoDistribucion.Estado.EN_RUTA
    pedido.motivo_no_entrega = ""
    pedido.save(update_fields=["estado", "motivo_no_entrega", "actualizado_en"])
    return pedido


def entregar_pedido(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion:
    """La tienda recibió. **El stock ya salió** al despachar.

    Aquí empieza a correr el plazo de crédito: `fecha_entrega` es la fecha
    desde la que se cuentan los `dias_credito` de la tienda.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoEntregable.
    """
    pedido = obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    _exigir_que_este_en_ruta(pedido)

    pedido.estado = PedidoDistribucion.Estado.ENTREGADO
    # La restricción `pedido_distribucion_fechas_coherentes` impide que esto
    # quede antes de la fecha del pedido, pase por donde pase.
    pedido.fecha_entrega = timezone.now()
    pedido.save(update_fields=["estado", "fecha_entrega", "actualizado_en"])
    return pedido


@transaction.atomic
def marcar_no_entregado(
    *, pedido_id: int, negocio_id: int, usuario_id: int, motivo: str
) -> PedidoDistribucion:
    """El camión volvió con la mercancía: se devuelve al inventario en el acto.

    Lo que se devuelve sale del **neto del kardex**, no de las líneas del
    pedido. Un pedido que se despachó, no se pudo entregar y se volvió a
    despachar acumula −X, +X, −X: solo el neto sabe cuánto está fuera de verdad
    y de qué bodega salió. Sumar las líneas devolvería el doble, y es un error
    que solo aparece en producción semanas después.

    El motivo va a la nota de esos movimientos, que es donde alguien lo va a
    buscar cuando pregunte por qué subió el saldo sin que entrara mercancía.

    Raises:
        NoEncontradoEnEsteNegocio, MotivoObligatorio, PedidoNoEntregable.
    """
    if not motivo or not motivo.strip():
        raise MotivoObligatorio

    pedido = _bloquear(pedido_id=pedido_id, negocio_id=negocio_id)
    _exigir_que_este_en_ruta(pedido)

    consumo.devolver_lo_movido_por(
        referencia_tipo=REFERENCIA,
        referencia_id=pedido.id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=motivo.strip(),
    )

    pedido.estado = PedidoDistribucion.Estado.NO_ENTREGADO
    pedido.motivo_no_entrega = motivo.strip()
    pedido.save(update_fields=["estado", "motivo_no_entrega", "actualizado_en"])
    return pedido


def cancelar_pedido(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion:
    """Anula un pedido que todavía está en la bodega.

    Solo se puede desde `pendiente` o `no_entregado`, que son los dos estados
    en los que la mercancía no salió o ya volvió: no hay nada que devolver.

    **Desde `en_ruta` se rechaza** pidiendo marcar primero `no_entregado`: el
    atajo dejaría el saldo descontado para siempre, sin ninguna fila del kardex
    que explicara el regreso. Desde `entregado` tampoco — eso es una
    devolución, y es otra operación.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoCancelable.
    """
    pedido = obtener_pedido(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido.estado == PedidoDistribucion.Estado.EN_RUTA:
        raise PedidoNoCancelable(
            "Ese pedido va en el camión. Márcalo primero como no entregado, "
            "para que la mercancía vuelva a la bodega."
        )
    if not pedido.se_puede_despachar:
        raise PedidoNoCancelable(estado=pedido.estado)

    pedido.estado = PedidoDistribucion.Estado.CANCELADO
    pedido.save(update_fields=["estado", "actualizado_en"])
    return pedido


def _bloquear(*, pedido_id: int, negocio_id: int) -> PedidoDistribucion:
    """El pedido con su fila bloqueada, para lo que mueve inventario.

    Sin el bloqueo, dos despachos del mismo pedido a la vez pasarían los dos la
    comprobación de estado y descontarían la mercancía dos veces.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    pedido = repositorio.bloquear(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido is None:
        raise NoEncontradoEnEsteNegocio
    return pedido


def _exigir_que_este_en_ruta(pedido: PedidoDistribucion) -> None:
    """Raises: PedidoNoEntregable: no va en el camión, así que no llegó ni volvió."""
    if pedido.estado != PedidoDistribucion.Estado.EN_RUTA:
        raise PedidoNoEntregable(estado=pedido.estado)


def _precios_congelados(*, lineas: list[LineaDePedidoDTO], negocio_id: int) -> dict[int, Decimal]:
    """El precio mayorista **del momento**, leído del catálogo.

    No viaja en la petición a propósito: si lo mandara quien pide, cualquiera
    podría fijar el precio de su propia mercancía. Y se copia a la línea porque
    cambiar mañana la lista de precios no puede reescribir las facturas de las
    tiendas de este mes.

    Aquí se valida cada línea, **antes** de `bulk_create`, que no ejecuta las
    validaciones de Python: una cantidad en cero saldría como `IntegrityError`
    y llegaría al cliente como un 500.

    Raises:
        PedidoSinLineas: alguna cantidad no es positiva.
        NoEncontradoEnEsteNegocio: algún producto es de otro negocio.
    """
    if any(linea.cantidad <= 0 for linea in lineas):
        raise PedidoSinLineas("Las cantidades del pedido deben ser mayores que cero.")

    ids = {linea.producto_id for linea in lineas}
    productos = repositorio_de_productos.del_negocio(negocio_id=negocio_id).filter(pk__in=ids)
    precios = {producto.id: producto.precio_mayorista for producto in productos}
    if len(precios) != len(ids):
        raise NoEncontradoEnEsteNegocio
    return precios

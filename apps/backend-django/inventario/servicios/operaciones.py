"""Las operaciones de inventario que se piden desde fuera.

Todas pasan por `aplicar_movimientos`: aquí solo se decide el signo, el tipo y
la referencia. El bloqueo, la comprobación de saldo y la escritura son cosa del
motor, y por eso hay un solo sitio donde el inventario se puede descuadrar.
"""

from decimal import Decimal

from django.db import transaction

from inventario.dtos import LineaDeMovimientoDTO, LineaDeProductoDTO
from inventario.excepciones import CantidadInvalida, MotivoObligatorio, MovimientoYaAnulado
from inventario.models import MovimientoInventario
from inventario.repositorios import movimientos as repositorio
from inventario.servicios.movimientos import aplicar_movimientos
from nucleo.excepciones import NoEncontradoEnEsteNegocio

Tipo = MovimientoInventario.Tipo
Referencia = MovimientoInventario.ReferenciaTipo


def registrar_entrada_de_mercancia(
    *,
    ubicacion_id: int,
    lineas: list[LineaDeProductoDTO],
    usuario_id: int,
    negocio_id: int,
    nota: str = "",
) -> list[MovimientoInventario]:
    """Recibe mercancía de un proveedor en una ubicación.

    Raises:
        CantidadInvalida, NoEncontradoEnEsteNegocio.
    """
    return aplicar_movimientos(
        lineas=_a_lineas(lineas, ubicacion_id=ubicacion_id, signo=1),
        tipo=Tipo.ENTRADA,
        referencia_tipo=Referencia.COMPRA,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=nota,
    )


def registrar_salida(
    *,
    ubicacion_id: int,
    lineas: list[LineaDeProductoDTO],
    usuario_id: int,
    negocio_id: int,
    nota: str = "",
) -> list[MovimientoInventario]:
    """Saca mercancía a mano, fuera de una venta.

    Las ventas **no** llaman aquí: para eso está `consumo.descontar_por_venta`,
    que además ata los movimientos al pedido que los originó.

    Raises:
        CantidadInvalida, NoEncontradoEnEsteNegocio, ExistenciasInsuficientes.
    """
    return aplicar_movimientos(
        lineas=_a_lineas(lineas, ubicacion_id=ubicacion_id, signo=-1),
        tipo=Tipo.SALIDA,
        referencia_tipo=Referencia.AJUSTE,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=nota,
    )


def registrar_merma(
    *,
    ubicacion_id: int,
    lineas: list[LineaDeProductoDTO],
    usuario_id: int,
    negocio_id: int,
    motivo: str,
) -> list[MovimientoInventario]:
    """Lo que se rompió, se derramó o se venció.

    Tiene tipo propio y no es "una salida con nota" porque la merma se mide y
    se compara contra la venta: con un `tipo` ese informe sale sin leer textos
    libres.

    Raises:
        MotivoObligatorio, CantidadInvalida, ExistenciasInsuficientes.
    """
    _exigir_motivo(motivo)
    return aplicar_movimientos(
        lineas=_a_lineas(lineas, ubicacion_id=ubicacion_id, signo=-1),
        tipo=Tipo.MERMA,
        referencia_tipo=Referencia.AJUSTE,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=motivo.strip(),
    )


@transaction.atomic
def transferir_entre_ubicaciones(
    *,
    producto_id: int,
    origen_id: int,
    destino_id: int,
    cantidad: Decimal,
    usuario_id: int,
    negocio_id: int,
    nota: str = "",
) -> list[MovimientoInventario]:
    """Mueve mercancía de un sitio a otro. **Son dos filas de kardex, no una.**

    Una negativa en el origen y otra positiva en el destino, con el mismo
    `referencia_id`. Si fuera una sola fila con origen y destino, cada consulta
    de saldo tendría que tratar los traslados como caso especial.

    El `referencia_id` se pone **después** de insertar, porque es el id de la
    propia fila de salida y no existe hasta entonces.

    Raises:
        CantidadInvalida: la cantidad no es positiva, u origen y destino son el
            mismo sitio.
        NoEncontradoEnEsteNegocio, ExistenciasInsuficientes.
    """
    if cantidad <= 0:
        raise CantidadInvalida("La cantidad a trasladar debe ser mayor que cero.")
    if origen_id == destino_id:
        raise CantidadInvalida("El origen y el destino son la misma ubicación.")

    movimientos = aplicar_movimientos(
        lineas=[
            LineaDeMovimientoDTO(
                producto_id=producto_id, ubicacion_id=origen_id, cantidad=-cantidad
            ),
            LineaDeMovimientoDTO(
                producto_id=producto_id, ubicacion_id=destino_id, cantidad=cantidad
            ),
        ],
        tipo=Tipo.TRASLADO,
        referencia_tipo=Referencia.TRASLADO,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=nota,
    )

    salida = next(movimiento for movimiento in movimientos if movimiento.cantidad < 0)
    repositorio.fijar_referencia(
        movimiento_ids=[movimiento.id for movimiento in movimientos],
        referencia_id=salida.id,
    )
    for movimiento in movimientos:
        movimiento.referencia_id = salida.id
    return movimientos


@transaction.atomic
def anular_movimiento(
    *, movimiento_id: int, negocio_id: int, usuario_id: int, motivo: str
) -> MovimientoInventario:
    """Deshace un movimiento creando su contrario. **Nunca borra nada.**

    Anular una entrada **puede fallar** con `ExistenciasInsuficientes`, y está
    bien: si la mercancía que entró de más ya se vendió, deshacer la entrada
    dejaría el saldo en negativo. Primero se cuadra con un ajuste.

    Que ya esté anulado se detecta sin tocar el esquema: la anulación se
    escribe con `referencia_tipo="ajuste"` y el id del movimiento anulado, y no
    choca con un ajuste manual, que lleva la referencia vacía.

    Raises:
        NoEncontradoEnEsteNegocio, MotivoObligatorio, MovimientoYaAnulado,
        ExistenciasInsuficientes.
    """
    _exigir_motivo(motivo)
    original = repositorio.obtener_del_negocio(movimiento_id=movimiento_id, negocio_id=negocio_id)
    if original is None:
        raise NoEncontradoEnEsteNegocio
    if repositorio.esta_anulado(movimiento_id=movimiento_id, negocio_id=negocio_id):
        raise MovimientoYaAnulado

    contrarios = aplicar_movimientos(
        lineas=[
            LineaDeMovimientoDTO(
                producto_id=original.producto_id,
                ubicacion_id=original.ubicacion_id,
                cantidad=-original.cantidad,
            )
        ],
        tipo=Tipo.AJUSTE,
        referencia_tipo=Referencia.AJUSTE,
        referencia_id=original.id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=motivo.strip(),
    )
    return contrarios[0]


def _a_lineas(
    lineas: list[LineaDeProductoDTO], *, ubicacion_id: int, signo: int
) -> list[LineaDeMovimientoDTO]:
    """Pone el signo. Quien llama dice "tres cervezas"; el signo lo decide aquí."""
    return [
        LineaDeMovimientoDTO(
            producto_id=linea.producto_id,
            ubicacion_id=ubicacion_id,
            cantidad=signo * linea.cantidad,
        )
        for linea in lineas
    ]


def _exigir_motivo(motivo: str) -> None:
    if not motivo or not motivo.strip():
        raise MotivoObligatorio

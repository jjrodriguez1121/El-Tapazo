"""La única puerta que usan los dos canales de venta.

`eventos` y `distribucion` **no llaman al motor directamente**: llaman aquí. Así
el signo, el tipo y la forma de devolver lo que se movió se deciden una vez, y
no una vez por canal.
"""

from decimal import Decimal

from inventario.dtos import LineaDeMovimientoDTO, LineaDeProductoDTO
from inventario.excepciones import CantidadInvalida
from inventario.models import MovimientoInventario
from inventario.repositorios import movimientos as repositorio
from inventario.servicios.movimientos import aplicar_movimientos


def descontar_por_venta(
    *,
    lineas: list[LineaDeProductoDTO],
    ubicacion_id: int,
    referencia_tipo: str,
    referencia_id: int,
    usuario_id: int,
    negocio_id: int,
) -> list[MovimientoInventario]:
    """Saca de una vez todo lo que lleva una venta.

    **Si una sola línea no alcanza, no sale ninguna**: media comanda descontada
    es peor que ninguna. Lo garantiza la transacción del motor.

    Raises:
        CantidadInvalida, NoEncontradoEnEsteNegocio, ExistenciasInsuficientes.
    """
    return aplicar_movimientos(
        lineas=[
            LineaDeMovimientoDTO(
                producto_id=linea.producto_id,
                ubicacion_id=ubicacion_id,
                cantidad=-linea.cantidad,
            )
            for linea in lineas
        ],
        tipo=MovimientoInventario.Tipo.SALIDA,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
    )


def devolver_lo_movido_por(
    *,
    referencia_tipo: str,
    referencia_id: int,
    usuario_id: int,
    negocio_id: int,
    nota: str = "",
) -> list[MovimientoInventario]:
    """Devuelve al inventario **el neto que el kardex dice que movió esa referencia**.

    Lo importante es que lee el kardex y no las líneas del pedido. Un pedido
    mayorista que se despachó, no se pudo entregar y se volvió a despachar
    acumula −X, +X, −X: solo el neto sabe cuánto está fuera de verdad y de qué
    bodega salió. Sumar las líneas del pedido devolvería el doble, y es un
    error que solo aparece en producción semanas después.

    Como los movimientos que crea llevan la misma referencia, llamarla dos
    veces no devuelve nada la segunda: el neto ya es cero.

    Devuelve una lista vacía si esa referencia no tiene nada fuera.

    Raises:
        CantidadInvalida: esa referencia **sumó** stock en vez de sacarlo. Los
            dos canales que usan esta puerta solo sacan mercancía, así que eso
            sería un caso nuevo que hay que pensar antes de etiquetarlo como
            una devolución.
    """
    netos = repositorio.neto_por_referencia(
        referencia_tipo=referencia_tipo, referencia_id=referencia_id, negocio_id=negocio_id
    )
    lineas = []
    for fila in netos:
        neto: Decimal = fila["neto"]
        if neto == 0:
            continue
        if neto > 0:
            raise CantidadInvalida(
                "Esa operación añadió mercancía al inventario; no se puede devolver."
            )
        lineas.append(
            LineaDeMovimientoDTO(
                producto_id=fila["producto_id"],
                ubicacion_id=fila["ubicacion_id"],
                cantidad=-neto,
            )
        )

    if not lineas:
        return []

    return aplicar_movimientos(
        lineas=lineas,
        tipo=MovimientoInventario.Tipo.ENTRADA,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        usuario_id=usuario_id,
        negocio_id=negocio_id,
        nota=nota,
    )

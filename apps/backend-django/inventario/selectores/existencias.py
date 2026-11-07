"""Lecturas del inventario."""

from decimal import Decimal

from django.db.models import DecimalField, F, QuerySet

from inventario.models import Existencia, MovimientoInventario
from inventario.repositorios import existencias as repositorio
from inventario.repositorios import movimientos as repositorio_de_movimientos

# El producto de dos DecimalField(12, 2) no cabe en 12 dígitos, de ahí el 24.
TIPO_DEL_IMPORTE = DecimalField(max_digits=24, decimal_places=4)


def existencias_del_negocio(*, negocio_id: int) -> QuerySet[Existencia]:
    """Todo el inventario de la única bodega del negocio."""
    return repositorio.del_negocio(negocio_id=negocio_id).select_related(
        "producto", "producto__categoria"
    )


def productos_bajo_minimo(*, negocio_id: int) -> QuerySet[Existencia]:
    """Lo que hay que reponer, por sitio.

    Solo mira las filas con mínimo puesto: un cero es "sin alerta", no "alerta
    siempre". Las escoge el índice parcial `existencia_con_minimo_idx`, que
    existe justo para que este informe no escanee la tabla entera.
    """
    return (
        repositorio.del_negocio(negocio_id=negocio_id)
        .filter(cantidad_minima__gt=0, cantidad_disponible__lt=F("cantidad_minima"))
        .select_related("producto")
    )


def kardex_de_un_producto(*, producto_id: int, negocio_id: int) -> QuerySet[MovimientoInventario]:
    """Toda la historia de un producto, de lo más reciente a lo más viejo.

    Usa `movimiento_producto_fecha_idx`, que es la consulta para la que existe.
    """
    return repositorio_de_movimientos.de_un_producto(
        producto_id=producto_id, negocio_id=negocio_id
    ).select_related("usuario")


def movimientos_de_una_referencia(
    *, referencia_tipo: str, referencia_id: int, negocio_id: int
) -> QuerySet[MovimientoInventario]:
    """De un pedido —o de un traslado— a las filas de kardex que generó."""
    return repositorio_de_movimientos.de_una_referencia(
        referencia_tipo=referencia_tipo, referencia_id=referencia_id, negocio_id=negocio_id
    ).select_related("producto", "usuario")


def valorizacion_del_inventario(*, negocio_id: int) -> Decimal:
    """Lo que vale el inventario a precio de costo.

    Lo multiplica y lo suma la base de datos: traerse las filas a Python para
    hacer la cuenta es el antipatrón explícito de las reglas.
    """
    total = repositorio.valor_total(negocio_id=negocio_id, tipo_del_importe=TIPO_DEL_IMPORTE)
    return total if total is not None else Decimal("0.00")

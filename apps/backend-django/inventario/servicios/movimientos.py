"""El motor del kardex: la función por la que pasa **todo** movimiento.

`movimientos_inventario` es la fuente de verdad y `existencias` un saldo
cacheado. Los dos se escriben aquí, en la misma transacción, y no hay otro
camino: si algún día el saldo se desvía del kardex, el bug está en este
archivo y en ningún otro.

Cuatro decisiones de este módulo que parecen detalles y no lo son:

1. **La suficiencia se comprueba contra el saldo cacheado, no contra el
   kardex.** No es por ahorrarse una suma: un `SUM` sobre el kardex **no
   bloquea nada**, y en `READ COMMITTED` —el nivel por defecto— dos meseros
   vendiendo la última caja calcularían el mismo total, los dos pasarían la
   comprobación y los dos insertarían. La fila de `Existencia` no es solo un
   caché: es la fila sobre la que se serializa la concurrencia. Quitarla
   obligaría a inventarla.

2. **Las filas se bloquean siempre en el mismo orden**, ordenadas por la clave
   `(producto_id, ubicacion_id)`. Si una función bloqueara "primero el origen y
   luego el destino", un traslado A→B y otro B→A se esperarían para siempre.

3. **La clave de orden es esa y no `existencia.id`**, porque la fila puede no
   existir todavía y entonces no hay id por el que ordenar.

4. **Si salta `existencia_no_negativa`, es un bug** —el caché se desvió del
   kardex— y no se captura para convertirlo en un mensaje amable: eso
   escondería justo lo que el sistema existe para detectar. Que suba y quede en
   los logs con su traza.
"""

from collections import defaultdict
from decimal import Decimal

from django.db import IntegrityError, transaction

from catalogo.repositorios import productos as repositorio_de_productos
from inventario.dtos import LineaDeMovimientoDTO
from inventario.excepciones import CantidadInvalida, ExistenciasInsuficientes
from inventario.models import Existencia, MovimientoInventario
from inventario.repositorios import existencias as repositorio
from inventario.repositorios import movimientos as repositorio_de_movimientos
from inventario.repositorios import ubicaciones as repositorio_de_ubicaciones
from nucleo.excepciones import NoEncontradoEnEsteNegocio

SIN_EXISTENCIAS = Decimal("0.00")


@transaction.atomic
def aplicar_movimientos(
    *,
    lineas: list[LineaDeMovimientoDTO],
    tipo: str,
    referencia_tipo: str,
    usuario_id: int,
    negocio_id: int,
    referencia_id: int | None = None,
    nota: str = "",
) -> list[MovimientoInventario]:
    """Aplica varias líneas de kardex y ajusta los saldos, todo o nada.

    El tipo y la referencia son de la operación entera: las dos filas de un
    traslado son el mismo traslado.

    Raises:
        CantidadInvalida: una línea en cero, o dos que se anulan entre sí.
        NoEncontradoEnEsteNegocio: algún producto o ubicación es de otro negocio.
        ExistenciasInsuficientes: el saldo quedaría en negativo.
    """
    consolidadas = _consolidar(lineas)
    _comprobar_que_todo_es_del_negocio(claves=consolidadas.keys(), negocio_id=negocio_id)

    movimientos = []
    # Ordenar es lo que fija el orden de bloqueo y evita los interbloqueos.
    for (producto_id, ubicacion_id), cantidad in sorted(consolidadas.items()):
        existencia = _bloquear_o_crear(
            producto_id=producto_id,
            ubicacion_id=ubicacion_id,
            negocio_id=negocio_id,
            cantidad=cantidad,
        )
        _comprobar_suficiencia(existencia=existencia, producto_id=producto_id, cantidad=cantidad)

        repositorio.sumar(existencia_id=existencia.id, cantidad=cantidad)
        movimientos.append(
            MovimientoInventario(
                negocio_id=negocio_id,
                producto_id=producto_id,
                ubicacion_id=ubicacion_id,
                tipo=tipo,
                cantidad=cantidad,
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
                usuario_id=usuario_id,
                nota=nota,
            )
        )
    return repositorio_de_movimientos.crear_en_lote(movimientos=movimientos)


def _consolidar(lineas: list[LineaDeMovimientoDTO]) -> dict[tuple[int, int], Decimal]:
    """Suma las líneas repetidas del mismo par producto/ubicación.

    Una comanda con "2 Águila" y "3 Águila" son **cinco** unidades que salen,
    no dos operaciones sobre la misma fila con el saldo leído a destiempo.

    Raises:
        CantidadInvalida: una línea en cero, o varias cuyo neto es cero. Lo
            segundo significa que quien llamó mandó líneas que se contradicen,
            y dejarlas pasar en silencio escondería el error.
    """
    if not lineas:
        raise CantidadInvalida("No hay nada que mover.")

    consolidadas: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    for linea in lineas:
        if linea.cantidad == 0:
            raise CantidadInvalida("Un movimiento de cero no es un movimiento.")
        consolidadas[(linea.producto_id, linea.ubicacion_id)] += linea.cantidad

    if any(cantidad == 0 for cantidad in consolidadas.values()):
        raise CantidadInvalida("Hay líneas del mismo producto que se anulan entre sí.")
    return dict(consolidadas)


def _comprobar_que_todo_es_del_negocio(*, claves, negocio_id: int) -> None:
    """Sin esto, mandando ids ajenos se movería el inventario de otro negocio."""
    productos = {producto_id for producto_id, _ in claves}
    ubicaciones = {ubicacion_id for _, ubicacion_id in claves}
    if not repositorio_de_productos.todos_son_del_negocio(
        producto_ids=productos, negocio_id=negocio_id
    ):
        raise NoEncontradoEnEsteNegocio
    if not repositorio_de_ubicaciones.todas_son_del_negocio(
        ubicacion_ids=ubicaciones, negocio_id=negocio_id
    ):
        raise NoEncontradoEnEsteNegocio


def _bloquear_o_crear(
    *, producto_id: int, ubicacion_id: int, negocio_id: int, cantidad: Decimal
) -> Existencia | None:
    """La fila del saldo, bloqueada. La crea en cero si hace falta y suma.

    Con un movimiento **negativo no se crea nada**: sin fila el disponible es
    cero, así que la venta no puede salir. Crear filas en cero cada vez que
    alguien intenta vender algo que no hay llenaría la tabla de basura.
    """
    existencia = repositorio.bloquear(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )
    if existencia is not None:
        return existencia
    if cantidad < 0:
        return None

    # El bloqueo de arriba no protege la creación: un `select_for_update()`
    # sobre una fila que no existe no bloquea nada. Quien protege es la
    # restricción `existencia_unica_por_producto_y_ubicacion`, y por eso el
    # `IntegrityError` se captura dentro de un `atomic()` **anidado**: sin ese
    # savepoint, el error aborta la transacción externa entera y todo lo que
    # venga después estalla con `TransactionManagementError`.
    try:
        with transaction.atomic():
            repositorio.crear_en_cero(
                producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
            )
    except IntegrityError:
        # Otra transacción la creó primero. No es un error: la queremos igual.
        pass

    # Se relee siempre, ya bloqueada: la fila puede ser la nuestra o la suya.
    return repositorio.bloquear(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )


def _comprobar_suficiencia(
    *, existencia: Existencia | None, producto_id: int, cantidad: Decimal
) -> None:
    """Raises: ExistenciasInsuficientes: el saldo quedaría en negativo."""
    disponible = SIN_EXISTENCIAS if existencia is None else existencia.cantidad_disponible
    if disponible + cantidad < 0:
        raise ExistenciasInsuficientes(
            producto_id=producto_id,
            solicitado=str(-cantidad),
            disponible=str(disponible),
        )

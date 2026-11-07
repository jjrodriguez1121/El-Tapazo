"""Pruebas de concurrencia del kardex.

Es lo único difícil del inventario y lo que no se puede probar de otra forma:
sin ellas, el descuadre aparece la primera noche con dos meseros y no en el CI.

Van en su propio archivo por tres razones, y las tres son necesidades técnicas,
no gusto:

* **`transaction=True`**: sin commits de verdad los hilos no se ven entre sí.
  A cambio, Django trunca las tablas entre pruebas y esto es lento — de ahí el
  marcador `lento`, declarado en `pyproject.toml` porque el proyecto corre con
  `--strict-markers`.
* **`connection.close()` en el `finally`** de cada hilo: cada uno abre su
  conexión y, sin cerrarla, la prueba se cuelga al limpiar.
* **`Barrier(2, timeout=...)` con tiempo límite**: si un hilo muere antes de
  llegar, sin el límite la suite se queda esperando para siempre en vez de
  fallar.
"""

import threading
from decimal import Decimal

import pytest
from django.db import connection

from catalogo.pruebas.fabricas import FabricaDeProducto
from inventario.dtos import LineaDeProductoDTO
from inventario.excepciones import ExistenciasInsuficientes
from inventario.models import Existencia, MovimientoInventario
from inventario.pruebas.fabricas import FabricaDeExistencia, FabricaDeUbicacion
from inventario.servicios import consumo, operaciones

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.lento]

SEGUNDOS_DE_ESPERA = 10


def _a_la_vez(*tareas):
    """Corre las tareas en paralelo y devuelve lo que dio cada una.

    Si una lanza una excepción, se devuelve la excepción en vez de propagarla:
    la gracia de estas pruebas es comprobar **cuál** de las dos falló.
    """
    barrera = threading.Barrier(len(tareas), timeout=SEGUNDOS_DE_ESPERA)
    resultados: list = [None] * len(tareas)

    def correr(posicion: int, tarea) -> None:
        try:
            barrera.wait()
            resultados[posicion] = tarea()
        except Exception as error:  # noqa: BLE001 — se inspecciona en el assert
            resultados[posicion] = error
        finally:
            # Sin esto la prueba se cuelga al limpiar: cada hilo abrió la suya.
            connection.close()

    hilos = [
        threading.Thread(target=correr, args=(posicion, tarea))
        for posicion, tarea in enumerate(tareas)
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=SEGUNDOS_DE_ESPERA)

    assert not any(hilo.is_alive() for hilo in hilos), "Un hilo se quedó colgado"
    return resultados


def test_dos_ventas_del_ultimo_producto_solo_una_pasa(negocio, administrador):
    """La razón de existir del `select_for_update`.

    Sin el bloqueo los dos hilos leerían "queda 1", los dos pasarían la
    comprobación y el saldo acabaría en −1.
    """
    existencia = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("1.00"))

    def vender(referencia_id: int):
        return consumo.descontar_por_venta(
            lineas=[
                LineaDeProductoDTO(producto_id=existencia.producto_id, cantidad=Decimal("1.00"))
            ],
            ubicacion_id=existencia.ubicacion_id,
            referencia_tipo=MovimientoInventario.ReferenciaTipo.PEDIDO_EVENTO,
            referencia_id=referencia_id,
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    resultados = _a_la_vez(lambda: vender(1), lambda: vender(2))

    fallos = [r for r in resultados if isinstance(r, ExistenciasInsuficientes)]
    exitos = [r for r in resultados if isinstance(r, list)]
    assert len(exitos) == 1, f"Debería pasar exactamente una venta: {resultados}"
    assert len(fallos) == 1, f"Debería fallar exactamente una venta: {resultados}"

    existencia.refresh_from_db()
    assert existencia.cantidad_disponible == Decimal("0.00")
    assert MovimientoInventario.objects.count() == 1


def test_dos_entradas_del_mismo_producto_nuevo_no_duplican_la_existencia(negocio, administrador):
    """El camino del savepoint.

    Un `select_for_update()` sobre una fila que no existe **no bloquea nada**:
    los dos hilos ven que no hay fila y los dos intentan crearla. Quien evita la
    duplicada es la restricción única, y el `IntegrityError` que salta se
    captura en un `atomic()` anidado para no abortar la transacción entera.
    """
    producto = FabricaDeProducto(negocio=negocio)
    bodega = FabricaDeUbicacion(negocio=negocio)

    def entrar(cantidad: str):
        return operaciones.registrar_entrada_de_mercancia(
            ubicacion_id=bodega.id,
            lineas=[LineaDeProductoDTO(producto_id=producto.id, cantidad=Decimal(cantidad))],
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    resultados = _a_la_vez(lambda: entrar("10.00"), lambda: entrar("5.00"))

    errores = [r for r in resultados if isinstance(r, Exception)]
    assert not errores, f"Las dos entradas deberían pasar: {errores}"

    existencias = Existencia.objects.filter(producto=producto, ubicacion=bodega)
    assert existencias.count() == 1, "Se duplicó la fila de existencias"
    assert existencias.get().cantidad_disponible == Decimal("15.00")


def test_dos_traslados_cruzados_no_se_bloquean_entre_si(negocio, administrador):
    """A→B y B→A a la vez.

    Si el orden de bloqueo fuera "primero el origen, luego el destino", cada
    hilo tendría la fila que el otro espera y se quedarían así para siempre.
    Con el orden fijo por `(producto_id, ubicacion_id)` los dos toman las filas
    en el mismo orden y el segundo simplemente espera.

    Si hubiera interbloqueo, esta prueba **falla** por el `timeout` del `join`
    en vez de colgar la suite.
    """
    en_a = FabricaDeExistencia(negocio=negocio, cantidad_disponible=Decimal("10.00"))
    bodega_b = FabricaDeUbicacion(negocio=negocio)
    FabricaDeExistencia(
        negocio=negocio,
        producto=en_a.producto,
        ubicacion=bodega_b,
        cantidad_disponible=Decimal("10.00"),
    )

    def trasladar(origen_id: int, destino_id: int):
        return operaciones.transferir_entre_ubicaciones(
            producto_id=en_a.producto_id,
            origen_id=origen_id,
            destino_id=destino_id,
            cantidad=Decimal("3.00"),
            usuario_id=administrador.id,
            negocio_id=negocio.id,
        )

    resultados = _a_la_vez(
        lambda: trasladar(en_a.ubicacion_id, bodega_b.id),
        lambda: trasladar(bodega_b.id, en_a.ubicacion_id),
    )

    errores = [r for r in resultados if isinstance(r, Exception)]
    assert not errores, f"Los dos traslados deberían pasar: {errores}"

    total = sum(
        existencia.cantidad_disponible
        for existencia in Existencia.objects.filter(producto=en_a.producto)
    )
    assert total == Decimal("20.00"), "Un traslado no puede cambiar el total del negocio"

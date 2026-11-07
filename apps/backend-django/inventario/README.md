# App: `inventario`

Existencias y su historial: ubicaciones físicas, saldo por producto y el kardex de movimientos (la fuente de verdad del inventario).

**Modelos:** `Ubicacion` · `Existencia` · `MovimientoInventario`.

`Existencia` es el saldo de un producto en una ubicación, y es un **caché**:
la fuente de verdad es el kardex (`MovimientoInventario`), que guarda cada
entrada y cada salida. Si los dos discrepan, manda el kardex.

## Qué se puede hacer

`/api/v1/inventario/`

| Recurso | Quién | Qué |
| --- | --- | --- |
| `GET existencias/` · `GET existencias/bajo-minimo/` | **todo el equipo** | Mirar si queda cerveza, y qué hay que reponer |
| `POST existencias/minimo/` | admin | Fijar el punto de reposición |
| `ubicaciones/` | leer: equipo · escribir: admin | Bodegas y puntos de venta |
| `movimientos/` | admin | El kardex, y las operaciones que lo escriben |
| `GET valorizacion/` | admin | Lo que vale el inventario a costo |

Las operaciones cuelgan de `movimientos/`: `entradas/`, `salidas/`, `mermas/`,
`traslados/`, `ajustes/`, `reconstruccion/` y `{id}/anulacion/`.

**Los meseros leen existencias pero no las mueven a mano**: al vender se mueven
solas, desde `servicios/consumo.py`.

## Lo que hay que entender antes de tocar esto

**Todo movimiento pasa por `servicios/movimientos.aplicar_movimientos`.** Es el
único sitio donde se escriben a la vez el kardex y el saldo cacheado, y por eso
es el único donde el inventario se puede descuadrar. Cuatro cosas de ese archivo
parecen detalles y no lo son:

1. **La suficiencia se comprueba contra el saldo cacheado, no contra el
   kardex.** No es por ahorrarse una suma: un `SUM` no bloquea nada, y dos
   meseros vendiendo la última caja pasarían los dos la comprobación. La fila de
   `Existencia` es sobre la que se serializa la concurrencia.
2. **Las filas se bloquean siempre en el mismo orden**, por `(producto_id,
   ubicacion_id)`. "Primero el origen y luego el destino" colgaría dos traslados
   cruzados para siempre.
3. **`select_for_update()` sobre una fila que no existe no bloquea nada.** Quien
   evita la existencia duplicada es la restricción única, y el `IntegrityError`
   se captura en un `atomic()` **anidado** para no abortar la transacción entera.
4. **Si salta `existencia_no_negativa`, es un bug** y no se captura: esconderlo
   taparía justo lo que el sistema existe para detectar.

**`ajustar_existencias` y `reconstruir_saldo_desde_kardex` se parecen y no son
lo mismo.** El primero arregla el estante y **crea** un movimiento de ajuste con
motivo; el segundo arregla el caché y **no crea ninguno**, porque inventarlo
falsearía la historia de la mercancía.

Los dos canales de venta entran por `servicios/consumo.py`, nunca al motor
directamente. `devolver_lo_movido_por` lee el **neto del kardex**, no las líneas
del pedido: un pedido despachado, no entregado y vuelto a despachar acumula
−X, +X, −X, y sumar las líneas devolvería el doble.

Las pruebas de concurrencia van aparte, en `pruebas/test_concurrencia.py`, con
el marcador `lento`.

## Carpetas

| Carpeta | Qué va aquí |
| --- | --- |
| `api/` | Vistas, serializers y routers (capa HTTP). |
| `dtos/` | Objetos de transferencia de datos entre capas (dataclasses). |
| `excepciones/` | Excepciones propias del dominio de esta app. |
| `migrations/` | Migraciones de base de datos (nombre exigido por Django). |
| `permisos/` | Permisos de DRF específicos de esta app. |
| `repositorios/` | Acceso a datos: consultas al ORM aisladas del resto. |
| `selectores/` | Lecturas / consultas de negocio. |
| `servicios/` | Reglas de negocio y escrituras. |
| `pruebas/` | Pruebas de esta app. |
| `validadores/` | Validaciones reutilizables del dominio. |

Reglas de código: [`varios/reglas/`](../../../varios/reglas/README.md) ·
Arquitectura: [`docs/backend/estructura.md`](../../../docs/backend/estructura.md)

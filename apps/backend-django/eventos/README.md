# App: `eventos`

Canal de venta en eventos/bar: la noche, las pulseras NFC, las cuentas por persona y grupo, las comandas y los pagos.

**Modelos:** `Evento` · `PulseraNfc` · `GrupoEvento` · `ClienteEvento` ·
`PedidoEvento` · `DetallePedidoEvento` · `AlertaConsumo` · `PagoEvento`.

La cadena es: `Evento` → `GrupoEvento` (la mesa) → `ClienteEvento` (la persona
con su pulsera) → `PedidoEvento` → `DetallePedidoEvento`.

Un `Evento` no es solo una fiesta: es **una jornada de venta que se abre y se
cierra**. En un negocio que abre a diario, es el día de hoy. La `PulseraNfc`
solo guarda el UID del chip y su condición física — a quién se le prestó vive
en `ClienteEvento`, una fila nueva cada vez.

Un `PedidoEvento` sin `ClienteEvento` es la **venta de mostrador**: se paga al
instante y no hay cuenta que cobrar después. Un `PagoEvento` salda el grupo
completo, la parte de una persona o una venta de mostrador — nunca dos cosas a
la vez, y la base de datos lo obliga.

## Qué se puede hacer

`/api/v1/eventos/` — el reparto de permisos es la decisión 6 del plan, más las
10 y 11:

| Acción | admin | cajero | mesero |
| --- | --- | --- | --- |
| Abrir y cerrar la caja (`jornadas/apertura`, `{id}/cierre`) | sí | sí | **no** |
| Abrir y cerrar grupos, abrir cuentas, asignar pulseras | sí | sí | sí |
| Tomar y entregar comandas | sí | sí | sí |
| Cobrar, liberar cuentas y **cancelar comandas** | sí | sí | **no** |
| Registrar pulseras y lectores de puerta | sí | **no** | **no** |

Además, `selectores/informes.py` calcula lo vendido y lo cobrado por la barra
en un rango de fechas. No tiene endpoint propio: lo consume el resumen por
canal de `negocios`, que suma este canal y el mayorista.

## Lo que hay que entender antes de tocar esto

**La jornada se abre sola.** `jornadas/apertura` devuelve la que esté en curso
en esa ubicación y, si no hay, la abre: nadie tiene que crear el evento a mano
cada mañana. La carrera se corta por partida doble —bloqueando la fila de
`Ubicacion` y con la restricción parcial de la base—, y el nombre sale de
`timezone.localdate()`, **nunca de `date.today()`**: una barra que abre a las
once de la noche partiría cada noche en dos jornadas mal nombradas.

**La comanda descuenta al crearse, no al entregarse** (decisión 1). Entre que
el mesero la toma y la sirve, la cerveza ya salió de la nevera. Sin existencias
se bloquea siempre, sin excepción para el administrador (decisión 2), y si
falta stock no queda ni el pedido.

**El precio se congela en la línea** leyendo `producto.precio_evento`. No viaja
en la petición a propósito: si lo mandara quien pide, cualquiera podría fijar
el precio de su propia cerveza.

**El cobro bloquea la cuenta y vuelve a comprobar `liberada_en` después del
bloqueo.** Dos cajeros cobrando la misma pulsera generarían dos pagos y la caja
cuadraría de más, y la restricción de la pulsera **no lo impide**: impide dos
asignaciones activas, no dos cierres.

**Cancelar devuelve el neto del kardex**, no las líneas del pedido — la misma
puerta que usa el mayoreo. Por eso cancelar dos veces no repone de más.

**El punto de control tiene su propio token.** `POST
puntos-de-control/consultar/` con `Authorization: Dispositivo <token>`. El
negocio sale del aparato, nunca de la petición; devuelve el nombre y el monto,
ni documento ni teléfono; y lleva freno de peticiones, porque cualquiera con un
lector de tres dólares podría ir preguntando cuánto debe cada persona del bar.
El token en claro se enseña **una sola vez**, al dar de alta el lector.

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

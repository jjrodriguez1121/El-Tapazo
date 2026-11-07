# App: `distribucion`

Canal de venta mayorista (B2B): tiendas cliente, sus pedidos y sus abonos.

**Modelos:** `ClienteDistribucion` · `PedidoDistribucion` ·
`DetallePedidoDistribucion` · `PagoDistribucion`.

Mismo catálogo que el bar, otro precio (`producto.precio_mayorista`) y, casi
siempre, crédito: entre `fecha_entrega` y los `dias_credito` de la tienda corre
su plazo. El `precio_unitario` de cada línea se congela al vender, para que
cambiar la lista de precios no reescriba las facturas del mes pasado.

## El ciclo de un pedido

```
pendiente ──despachar──► en_ruta ──entregar──► entregado
    ▲                       │
    │                  no entregar
    │                       ▼
    └───── despachar ── no_entregado ──► cancelado
```

- **El stock sale al despachar**, no al entregar: entre las dos cosas la
  mercancía va en el camión, o sea que ya no está en la bodega.
- **Si no se pudo entregar, vuelve en el acto** y el pedido se puede volver a
  despachar. Lo que se devuelve sale del *neto del kardex*, no de las líneas
  del pedido: tras un ciclo despacho → no entrega → despacho, sumar las líneas
  devolvería el doble.
- **Cancelar solo se puede con la mercancía en la bodega** (pendiente o no
  entregado). Desde «en ruta» hay que marcar primero la no entrega.
- **Aquí sí hay abonos**, al revés que en el bar: una tienda a 30 días paga en
  varias veces. Que la suma no pase del total lo comprueba el servicio
  bloqueando el pedido — es un agregado y no cabe en una restricción de fila.

Todo el módulo es de **administrador** (decisión 6 del plan de negocio).

## Endpoints

| Ruta | Para qué |
| --- | --- |
| `clientes/` | Alta, listado y corrección de tiendas. |
| `clientes/mora/` | A quién hay que cobrarle: se le pasó el plazo y debe. |
| `clientes/{id}/pedidos/` · `saldo/` · `desactivacion/` | Historial, deuda total y baja. |
| `pedidos/` | Tomar un pedido y listarlo (`?estado=en_ruta` es la ruta de hoy). |
| `pedidos/{id}/despacho/` · `entrega/` · `no-entrega/` · `cancelacion/` | El ciclo de arriba. |
| `pedidos/{id}/abonos/` · `saldo/` | Registrar abonos y ver lo que falta. |

Además, `selectores/informes.py` calcula lo facturado y lo abonado por las
tiendas en un rango de fechas. No tiene endpoint propio: lo consume el resumen
por canal de `negocios`.

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

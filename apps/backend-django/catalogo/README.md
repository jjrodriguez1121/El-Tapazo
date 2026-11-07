# App: `catalogo`

Catálogo del negocio: qué se vende, de qué tipo, a qué precio en cada canal y a
quién se le compra.

**Modelos:** `Categoria` · `Proveedor` · `Producto` · `ProductoProveedor`.

Un producto pertenece a una categoría y se le puede comprar a varios
proveedores: `ProductoProveedor` guarda el precio de compra de cada uno y cuál
es el habitual.

## Qué se puede hacer

`/api/v1/catalogo/` — **todo es de administrador** (decisión 6 del plan de
negocio): el catálogo cambia lo que el resto del equipo ve toda la noche.

| Recurso | Además del CRUD |
| --- | --- |
| `categorias/` | `POST {id}/desactivacion/` |
| `proveedores/` | `POST {id}/desactivacion/` |
| `productos/` | `POST {id}/precio/` · `POST {id}/desactivacion/` · `GET {id}/margen/` · `GET`/`POST {id}/proveedores/` · `DELETE`/`POST {id}/proveedores/{proveedor_id}/[principal/]` |

Dos cosas que conviene saber antes de tocar esto:

- **El SKU tiene formato obligatorio**: tres letras, un guion y de 3 a 6 cifras
  (`CER-001`). Se normaliza a mayúsculas antes de validar. Está en
  `validadores/sku.py`.
- **Cambiar un precio va aparte** de actualizar el producto, porque queda
  registrado quién lo hizo. Hoy ese rastro va **al log del servidor**, no a la
  base: `productos` no tiene columna de autoría y una columna solo guardaría el
  último cambio. Lo que hace falta es la bitácora de auditoría que
  [`diseno_base_datos.md`](../../../varios/bd/diseno_base_datos.md) §6.4 deja
  pendiente.

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

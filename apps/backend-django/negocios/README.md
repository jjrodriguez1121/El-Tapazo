# App: `negocios`

Negocios (la raíz del modelo de datos): casi todo lo demás cuelga de un negocio.

**Modelos:** `Negocio`.

Aquí viven dos cosas que no son del día a día de nadie:

- **La administración de la plataforma.** Dar de alta un negocio, corregir sus
  datos, suspenderlo y reactivarlo. Es del **staff** (`is_superuser`), que
  existe por encima de los negocios y no pertenece a ninguno. Un negocio nace
  vacío: a su primer administrador se le invita desde la terminal con
  `manage invitar_administrador`, y a partir de ahí él invita a su equipo. No
  hay registro público, y es a propósito.
- **El resumen de ventas por canal.** Cuánto puso la barra y cuánto el mayoreo
  en un rango de fechas. Está aquí porque el dato que cruza los dos canales es
  el negocio; cada canal calcula lo suyo en su propia app
  (`eventos/selectores/informes.py` y `distribucion/selectores/informes.py`) y
  este módulo solo suma. No hay —ni hará falta— una app `informes`.

Suspender **no borra nada**: los datos siguen enteros y lo único que cambia es
que su gente deja de poder entrar, porque el inicio de sesión mira el estado y
responde `negocio_suspendido`.

## Endpoints

| Ruta | Quién | Para qué |
| --- | --- | --- |
| `negocios/` | Staff | Listar y dar de alta negocios. |
| `negocios/{id}/` | Staff | Ver y corregir uno. |
| `negocios/{id}/suspension/` · `reactivacion/` | Staff | Sacarlo y devolverlo a la operación. |
| `negocios/mio/` | Cualquiera del equipo | El negocio de quien pregunta. |
| `negocios/informes/ventas/` | Administrador | Vendido y cobrado por canal (`?desde=&hasta=`). |

`vendido` y `cobrado` son dos números distintos a propósito: en la barra casi
coinciden —se cobra la misma noche—, y en el mayoreo no, porque se vende a
crédito.

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

# Convenciones del backend

---

## Nombres

| Elemento | Estilo | Ejemplo |
| --- | --- | --- |
| Apps y módulos | `snake_case`, en español y en plural cuando aplique | `negocios`, `movimientos_inventario.py` |
| Clases | `PascalCase` | `MovimientoInventario`, `ProductoSerializer` |
| Funciones y variables | `snake_case` | `registrar_entrada()`, `stock_actual` |
| Constantes | `MAYÚSCULAS` | `MAX_ITEMS_POR_ORDEN` |
| Modelos | Singular | `Producto`, no `Productos` |
| Endpoints | `kebab-case` en plural | `/api/v1/inventario/movimientos/` |

Acuerdo del equipo: **todo en español** — apps, modelos, campos, funciones,
carpetas y documentación. Las únicas excepciones son los nombres que exige
Django (`models.py`, `admin.py`, `apps.py`, `migrations/`, `password`,
`last_login`, `is_superuser`). Ver [reglas de Python y Django](../../varios/reglas/reglas-python-django.md).

---

## Estilo de código

Lo revisa `ruff` (linter + formateador), configurado en `pyproject.toml`:
línea de 100 caracteres, imports ordenados automáticamente.

```bash
./dev.sh lint      # revisar
./dev.sh format    # arreglar lo arreglable
```

---

## Modelos

- Heredar de `ModeloConFechas` (`nucleo/models.py`) cuando haga falta
  `creado_en`/`actualizado_en`, y de `ModeloDelNegocio` cuando la tabla cuelgue
  de un negocio: así la columna `negocio_id` se llama igual en todas.
- Siempre definir `class Meta` con `db_table`, `ordering` y `verbose_name`.
- **`db_table` obligatorio y en plural.** Sin él, Django nombra la tabla
  `app_modelo` (`usuarios_usuario`, `negocios_negocio`). Queremos los nombres
  del diseño: `usuarios`, `negocios`, `invitaciones`, `movimientos_inventario`.
- Siempre definir `__str__`.
- Usar `DecimalField` para dinero y cantidades, **nunca** `FloatField`.
- `related_name` explícito en las relaciones.
- Índices (`db_index=True` o `Meta.indexes`) en los campos por los que se
  filtra seguido (SKU, código de barras, fechas de movimiento).
- Nada de borrar físicamente registros de inventario: usar estados o marcas de
  anulación para no perder trazabilidad.

---

## Services

- Una función por caso de uso, con nombre de verbo.
- Reciben datos ya validados; no reciben `request`.
- Si escriben en varias tablas, envolver en `transaction.atomic()`.
- Lanzan excepciones del dominio (`excepciones/`), no `Response` ni `Http404`.
- No importan nada de `api/`: la dependencia va en un solo sentido
  (`api → servicios → repositorios → models`).

---

## API

- Usar `ViewSet` + `Router` para los CRUD; `APIView` para acciones puntuales.
- Versionar siempre bajo `/api/v1/`.
- Un serializer por caso: entrada y salida no tienen por qué ser el mismo.
- Paginar todos los listados (ya está por defecto: 20 por página).
- Documentar los endpoints con `drf-spectacular` (`@extend_schema`).
- Devolver los códigos correctos: `201` al crear, `204` al borrar,
  `400` en error de validación, `403` sin permisos, `404` si no existe.

---

## Migraciones

- Se generan con `./dev.sh makemigrations` y **se suben a git**.
- Una migración por cambio lógico, con nombre descriptivo:
  `./dev.sh makemigrations catalogo -n agregar_codigo_barras_a_producto`
- Nunca editar una migración que ya está en `main`: crear una nueva.
- Migraciones de datos: en un archivo aparte, con `RunPython` y su función
  inversa.

---

## Pruebas

- Con `pytest` + `pytest-django`, dentro de `pruebas/` de cada app.
- Un archivo por capa: `test_modelos.py`, `test_servicios.py`,
  `test_selectores.py`, `test_api.py`.
- Nombres explícitos: `def test_registrar_entrada_aumenta_el_stock():`
- Datos de prueba con `factory-boy`, no con fixtures JSON.
- Prioridad: los **servicios** son lo más importante de probar; ahí está el
  negocio.

```bash
./dev.sh test back
docker compose exec backend pytest catalogo -v
docker compose exec backend pytest --cov
```

---

## Variables de entorno

- Todo lo que cambie entre entornos o sea secreto se lee con `django-environ`.
- Cualquier variable nueva se agrega **también** a `.env.example` y al
  `compose.yaml`, para que al equipo no se le rompa nada al hacer `pull`.
- Nunca subir un `.env` real ni una `SECRET_KEY` de producción.

---

## Dependencias

- `requirements/base.txt` — lo que se necesita en todos los entornos.
- `requirements/local.txt` — herramientas de desarrollo.
- `requirements/production.txt` — servidor y estáticos.
- Fijar la versión (`==` o `~=`) para que todos instalemos lo mismo.
- Después de agregar una: `docker compose build backend`.

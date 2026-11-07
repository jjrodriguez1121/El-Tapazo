# Crear una app nueva

Receta para agregar un módulo de negocio (por ejemplo `ventas` o `informes`)
manteniendo la estructura del proyecto.

---

## 1. Crear la app

```bash
./dev.sh startapp ventas
```

Queda en `apps/backend-django/ventas/` con la estructura mínima de Django.

---

## 2. Completar la estructura del proyecto

```bash
docker compose exec backend bash -c '
cd /app/ventas
for d in api dtos excepciones permisos repositorios selectores servicios pruebas validadores; do
  mkdir -p $d && touch $d/__init__.py
done
touch README.md
'
```

---

## 3. Ajustar `apps.py`

```python
from django.apps import AppConfig


class VentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ventas"
    verbose_name = "Ventas"
```

---

## 4. Registrarla en la configuración

En `config/settings/base.py`, dentro de `LOCAL_APPS`:

```python
LOCAL_APPS = [
    "nucleo",
    "negocios",
    "usuarios",
    ...
    "ventas",     # <- nueva
]
```

---

## 5. Crear `urls.py` y engancharla

`ventas/urls.py`:

```python
app_name = "ventas"

urlpatterns = []
```

En `config/urls.py`, dentro de `api_v1_patterns`:

```python
path("ventas/", include("ventas.urls")),
```

---

## 6. Escribir el README de la app

`ventas/README.md`: para qué sirve el módulo y qué entidades maneja. Copiar la
tabla de carpetas de otra app para mantener el formato.

---

## 7. Verificar y migrar

```bash
./dev.sh manage check
./dev.sh makemigrations ventas
./dev.sh migrate
```

---

## 8. Agregarla a las pruebas

En `pyproject.toml`, sumar `"ventas"` a `testpaths` y a
`[tool.ruff.lint.isort] known-first-party`.

---

## Antes de crear una app, pregúntate

Una app nueva se justifica cuando el módulo tiene **sus propias entidades y sus
propias reglas**. Si solo son dos o tres campos más de algo que ya existe, va
dentro de la app que ya lo maneja. Demasiadas apps pequeñas hacen el proyecto
más difícil de seguir que unas pocas bien delimitadas.

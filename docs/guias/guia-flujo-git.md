# Guía de flujo de trabajo con Git

Acuerdo del equipo para no pisarnos el trabajo. Si tienes dudas, sigue los
bloques de comandos tal cual: están en el orden en que se usan.

---

## Ramas

| Rama | Para qué |
| --- | --- |
| `main` | Código estable, listo para mostrar o desplegar. **No se hace commit directo aquí.** |
| `dev` | Rama de integración: aquí se junta el trabajo de todos. |
| `feat/<nombre>` | Una funcionalidad nueva. |
| `fix/<nombre>` | Corrección de un error. |
| `docs/<nombre>` | Cambios solo de documentación. |
| `refactor/<nombre>` | Reorganizar código sin cambiar lo que hace. |
| `chore/<nombre>` | Configuración, dependencias, mantenimiento. |

El `<nombre>` va en minúsculas, en español, separado por guiones y describiendo
**qué** se hace, no quién lo hace:

```
feat/registro-de-productos
fix/calculo-de-stock
docs/guia-de-instalacion
```

---

# CÓMO HACER UN BUEN COMMIT

## Lo normal

```bash
git commit -m "<tipo>: <resumen corto>" -m "<explicación más larga, opcional>"
```

## Commit largo (editor)

```bash
git commit
```

Y en el editor escribes:

```
feat: estructura inicial del backend

Crear la configuración del proyecto Django
Agregar las apps usuarios, catalogo e inventario
Definir la estructura de carpetas por capas
Dejar el entorno listo para Docker
```

**Formato:** primera línea corta (máx. ~72 caracteres), en presente y sin punto
final. Después una línea en blanco y, si hace falta, el detalle en viñetas.

## Tipos de commit (`<tipo>`)

```
feat     # Funcionalidad nueva
fix      # Corrección de un error
refactor # Mejora del código sin cambiar el comportamiento
docs     # Documentación
test     # Pruebas
chore    # Mantenimiento / configuración / dependencias
style    # Solo formato (espacios, comas, sangría)
```

Opcionalmente se puede indicar el módulo entre paréntesis:

```
feat(catalogo): agregar modelo de producto
fix(inventario): corregir el cálculo de existencias disponibles
docs(guias): agregar la guía de instalación
chore(docker): actualizar postgres a la versión 18
```

## ¿Qué estamos commiteando?

**Siempre revisa antes de commitear.** No hagas `git add .` a ciegas:

```bash
git status        # qué archivos cambiaron
git diff          # qué cambió exactamente dentro de ellos
git add .         # o mejor: git add <archivo1> <archivo2>
git status        # confirmar qué quedó en verde (listo para el commit)
```

---

# FLUJO DE TRABAJO EN GITHUB

## 1. Crear la rama a partir de `dev`

```bash
git checkout dev
git fetch origin
git pull origin dev
git checkout -b feat/registro-de-productos
git push -u origin feat/registro-de-productos
```

> `git fetch` + `git pull` antes de crear la rama es lo que evita que trabajes
> sobre código viejo y termines con conflictos innecesarios.

## 2. Trabajar y commitear

```bash
git status
git diff
git add .
git commit -m "feat(catalogo): agregar el modelo de producto"
git push -u origin feat/registro-de-productos
```

Puedes repetir este paso todas las veces que quieras: es mejor **varios commits
pequeños** que uno gigante al final.

Antes de subir, revisa que no rompiste nada:

```bash
./dev.sh lint      # estilo en backend y frontend
./dev.sh test      # pruebas
```

## 3. Llevar los cambios a `dev`

```bash
git checkout dev
git fetch origin
git pull origin dev
git merge feat/registro-de-productos
```

## 4. Si hay conflictos, resolverlos

Git te dirá qué archivos chocaron:

```bash
git status                    # lista los archivos en conflicto
# ... abrir cada archivo y dejar la versión correcta ...
git add <archivo-resuelto>
git commit                    # confirma el merge
```

## 5. Subir `dev`

```bash
git push origin dev
```

## 6. Revisar GitHub Actions

Entra a la pestaña **Actions** del repositorio y mira el resultado del workflow
`CI` para tu push:

- ✅ **verde** — backend y frontend pasaron lint, pruebas y build. Listo.
- ❌ **rojo** — abre el job que falló, lee el log, corrige y vuelve a subir.

El CI corre automáticamente en cada push a `main` y a `dev`, y en cada pull
request. Lo que revisa es exactamente lo que puedes correr en tu máquina con
`./dev.sh lint` y `./dev.sh test`, así que si eso te pasa localmente, el CI
también debería pasar.

## 7. De `dev` a `main`

Solo cuando `dev` está estable y el CI en verde. Se hace por **pull request**
en GitHub (`dev` → `main`), con al menos una revisión de otra persona.

---

## Chuleta completa

```bash
# --- empezar algo nuevo ---
git checkout dev
git fetch origin
git pull origin dev
git checkout -b feat/mi-cambio
git push -u origin feat/mi-cambio

# --- mientras trabajas ---
git status
git diff
git add .
git commit -m "feat: descripción de lo que hice"
git push

# --- terminaste: integrar a dev ---
./dev.sh lint && ./dev.sh test
git checkout dev
git fetch origin
git pull origin dev
git merge feat/mi-cambio
git push origin dev

# --- revisar el CI en la pestaña Actions de GitHub ---
```

---

## Archivos que NO se suben

Ya están en `.gitignore`, pero para tenerlo claro:

- `.env` (los `.env.example` **sí** se suben)
- `node_modules/`, `dist/`
- `.venv/`, `__pycache__/`
- `media/` (archivos subidos por usuarios), `staticfiles/`

Sí se suben, en cambio:

- Las **migraciones** de Django: son parte del código.
- El **`package-lock.json`**: es lo que garantiza que todos instalemos
  exactamente las mismas versiones de npm. Si instalas una dependencia nueva,
  súbelo junto con el `package.json`.

---

## Después de traer cambios de otros

```bash
git pull origin dev

# Si cambiaron las dependencias, el Dockerfile o el package.json
./dev.sh up --build

# Si hay migraciones nuevas
./dev.sh migrate
```

# Guía de Docker

Cómo está armado el entorno y qué hacer cuando algo falla.

---

## Los tres servicios

```
┌─────────────────┐      ┌─────────────────┐      ┌──────────────┐
│  frontend       │─────>│  backend        │─────>│  db          │
│  React + Vite   │ HTTP │  Django + DRF   │ SQL  │ PostgreSQL 18│
│  node:24-alpine │      │  python:3.13    │      │              │
│  :5173          │      │  :8000          │      │  :5432       │
└─────────────────┘      └─────────────────┘      └──────────────┘
        red interna del proyecto: tapaso_net
```

Dentro de la red, los servicios se llaman entre sí por su **nombre**: el backend
conecta a la base de datos en el host `db`, no en `localhost`. Desde tu
navegador, en cambio, todo se ve en `localhost` con los puertos publicados.

---

## Archivos que definen el entorno

| Archivo | Qué hace |
| --- | --- |
| `dev.sh` | Script de arranque: elige puertos libres, actualiza el `.env` y llama a `docker compose`. |
| `compose.yaml` | Define los servicios de **desarrollo**: imágenes, puertos, volúmenes, variables. |
| `compose.prod.yaml` | Lo mismo para **producción** (sin volúmenes de código, con gunicorn y nginx). |
| `apps/backend-django/Dockerfile` | Cómo se construye la imagen del backend. Tiene etapas `development` y `production`. |
| `apps/frontend-react/Dockerfile` | Igual para el frontend: `development`, `builder` y `production`. |
| `.env` | Tus valores locales (puertos, claves). No se sube a git. |
| `docker/postgres/init/` | Scripts `.sql` que se ejecutan **solo la primera vez** que se crea la BD. |
| `docker/nginx/` | Config del proxy inverso opcional para producción. |

---

## Por qué hay etapas (`target`) en los Dockerfile

Un mismo Dockerfile sirve para desarrollo y producción:

- **development** — instala también las herramientas de desarrollo (pytest, ruff,
  debug toolbar) y espera que el código venga montado desde tu máquina, para que
  al guardar un archivo el servidor recargue solo.
- **production** — instala solo lo necesario, copia el código **dentro** de la
  imagen y corre con gunicorn (backend) o nginx (frontend), con un usuario sin
  privilegios.

`compose.yaml` usa `target: development`; `compose.prod.yaml` usa
`target: production`.

---

## Volúmenes: qué se guarda y qué no

| Volumen | Para qué |
| --- | --- |
| `./apps/backend-django:/app` | Monta tu código en el contenedor: editas en tu editor, el contenedor lo ve al instante. |
| `./apps/frontend-react:/app` | Igual para el frontend. |
| `/app/node_modules` (anónimo) | Evita que la carpeta `node_modules` de tu máquina (si existe) pise la que se instaló dentro del contenedor, que puede ser de otro sistema operativo. |
| `postgres_data` | Guarda los datos de PostgreSQL. **Sobrevive a `./dev.sh down`**; solo se borra con `./dev.sh clean`. |

> **Ojo con PostgreSQL 18:** desde esa versión la imagen oficial espera el
> volumen montado en `/var/lib/postgresql`, **no** en `/var/lib/postgresql/data`
> como en las versiones anteriores. Si se monta en la ruta vieja, el contenedor
> arranca y muere con un error largo sobre `pg_ctlcluster` y queda `unhealthy`.
> En `compose.yaml` ya está con la ruta correcta.

---

## Cuándo hay que reconstruir la imagen

Editar código **no** requiere reconstruir (está montado). Sí hay que hacer
`docker compose build <servicio>` cuando cambia:

- `requirements/*.txt` (backend)
- el `Dockerfile`

El `package.json` del frontend **no** lo necesita. Al arrancar, el contenedor
compara el `package-lock.json` con el de la última instalación y, si cambió,
instala antes de levantar Vite (`apps/frontend-react/scripts/entrypoint.sh`).
Hace falta porque `node_modules` vive en un volumen anónimo que sobrevive a los
reinicios: sin ese paso, a quien hace `pull` le llega el `package.json` nuevo
con los paquetes viejos.

```bash
docker compose build backend && docker compose up -d backend
```

---

## Problemas frecuentes

**El puerto ya está en uso**
```
Error ... port is already allocated
```
Otro programa ocupa ese puerto. Levanta con `./dev.sh up`: comprueba los puertos
antes de arrancar y toma el siguiente libre. Si prefieres fijarlo tú, cambia
`BACKEND_PORT`, `FRONTEND_PORT` o `POSTGRES_PORT_HOST` en el `.env` (y deja
`VITE_API_URL` apuntando al mismo puerto del backend).

Para ver quién tiene el puerto:
```bash
ss -ltnp | grep :8000      # Linux
lsof -i :8000              # macOS
```

**El backend no conecta a la base de datos**
```
could not connect to server: Connection refused
```
El backend espera a que la BD esté sana (`healthcheck`), pero si igual falla:
```bash
./dev.sh restart
./dev.sh logs db        # ver si la base arrancó bien
```
Revisa también que en el `.env` `POSTGRES_HOST` sea `db` y no `localhost`.

**Instalé un paquete y el contenedor dice que no existe**
Se instaló dentro del contenedor pero no quedó en la imagen. Agrégalo al
`requirements/*.txt` o `package.json` y reconstruye.

**Cambié un archivo y no se refleja**
Verifica que estás editando dentro de `apps/…` y que el servicio tiene el
volumen montado (`docker compose config` lo muestra). En Windows/WSL, activa
`usePolling` en `vite.config.js`.

**Migraciones en conflicto después de un merge**
```bash
docker compose exec backend python manage.py migrate <app> zero   # revertir esa app
docker compose exec backend python manage.py migrate
```
Si es un entorno de desarrollo desechable, lo más rápido es
`./dev.sh clean && ./dev.sh up`.

**Quiero empezar de cero**
```bash
./dev.sh clean                  # borra contenedores y datos
docker compose build --no-cache # reconstruye sin caché
./dev.sh up
```

**Se me llenó el disco de imágenes viejas**
```bash
docker system df       # ver cuánto ocupa
docker system prune -a # borrar lo que no se está usando (¡ojo, es global!)
```

---

## Comandos útiles de diagnóstico

```bash
docker compose config            # muestra la configuración final ya resuelta
docker compose ps                # estado de los servicios
docker compose logs -f backend   # logs en vivo de un servicio
docker compose top               # procesos dentro de los contenedores
docker stats                     # consumo de CPU/RAM
```

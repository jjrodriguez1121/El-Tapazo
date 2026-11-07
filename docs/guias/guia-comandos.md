# Guía de comandos

Chuleta del día a día. Todos los comandos se corren **desde la raíz del
repositorio**, con los contenedores levantados.

> Casi todo se hace con `./dev.sh` (usa `./dev.sh help` para verlos todos). La
> columna "comando equivalente" es lo que corre por debajo, por si necesitas
> algo que el script no cubre.
>
> `docker compose exec <servicio> <comando>` = "ejecuta esto **dentro** del
> contenedor". Si el contenedor está apagado, usa `run --rm` en vez de `exec`.

---

## Entorno completo

Lo normal es usar el script `./dev.sh`, que además elige puertos libres:

| Qué quiero | Script | Comando equivalente |
| --- | --- | --- |
| Levantar todo | `./dev.sh up` | `docker compose up -d` |
| Levantar reconstruyendo | `./dev.sh up --build` | `docker compose up -d --build` |
| Levantar un solo servicio | `./dev.sh up backend` | `docker compose up -d backend` |
| Apagar | `./dev.sh down` | `docker compose down` |
| Apagar y borrar la BD | `./dev.sh clean` | `docker compose down -v` |
| Ver estado y URLs | `./dev.sh status` | `docker compose ps` |
| Ver logs de todo | `./dev.sh logs` | `docker compose logs -f` |
| Ver logs de un servicio | `./dev.sh logs backend` | `docker compose logs -f backend` |
| Ver los puertos asignados | `./dev.sh ports` | — |
| Reiniciar | `./dev.sh restart` | `docker compose restart` |

> ¿Por qué el script y no `docker compose` a secas? Porque comprueba qué puertos
> están libres antes de levantar, los guarda en tu `.env` y mantiene
> `VITE_API_URL` apuntando al puerto correcto del backend. Si usas
> `docker compose` directo y un puerto está ocupado, el arranque falla con
> `port is already allocated`.

---

## Backend (Django)

| Qué quiero | Script | Comando equivalente |
| --- | --- | --- |
| Levantar solo el backend | `./dev.sh up backend` | `docker compose up -d backend` |
| Aplicar migraciones | `./dev.sh migrate` | `docker compose exec backend python manage.py migrate` |
| Crear migraciones | `./dev.sh makemigrations` | `docker compose exec backend python manage.py makemigrations` |
| Crear migraciones de una app | `./dev.sh makemigrations catalogo` | `... manage.py makemigrations catalogo` |
| Crear superusuario | `./dev.sh superuser` | `docker compose exec backend python manage.py createsuperuser` |
| Shell de Django | `./dev.sh shell` | `docker compose exec backend python manage.py shell` |
| Terminal dentro del contenedor | `./dev.sh sh backend` | `docker compose exec backend bash` |
| Crear una app nueva | `./dev.sh startapp ventas` | `docker compose exec backend python manage.py startapp ventas` |
| Cualquier comando de manage.py | `./dev.sh manage <comando>` | `docker compose exec backend python manage.py <comando>` |
| Correr las pruebas | `./dev.sh test back` | `docker compose exec backend pytest` |
| Pruebas de una app | — | `docker compose exec backend pytest catalogo` |
| Cobertura | — | `docker compose exec backend pytest --cov` |
| Revisar estilo | `./dev.sh lint` | `docker compose exec backend ruff check .` |
| Formatear código | `./dev.sh format` | `docker compose exec backend ruff format .` |
| Instalar una dependencia | Agrégala a `requirements/base.txt` y `./dev.sh up --build` | — |
| Ver SQL de una migración | `./dev.sh manage sqlmigrate catalogo 0001` | — |
| Verificar el proyecto | `./dev.sh manage check` | — |

---

## Frontend (React)

| Qué quiero | Script | Comando equivalente |
| --- | --- | --- |
| Levantar solo el frontend | `./dev.sh up frontend` | `docker compose up -d frontend` |
| Terminal dentro del contenedor | `./dev.sh sh frontend` | `docker compose exec frontend sh` |
| Instalar una dependencia | — | `docker compose exec frontend npm install axios` |
| Build de producción | — | `docker compose exec frontend npm run build` |
| Previsualizar el build | — | `docker compose exec frontend npm run preview` |
| Correr las pruebas | `./dev.sh test front` | `docker compose exec frontend npm run test` |
| Pruebas en modo watch | — | `docker compose exec frontend npm run test:watch` |
| Revisar estilo | `./dev.sh lint` | `docker compose exec frontend npm run lint` |
| Formatear código | `./dev.sh format` | `docker compose exec frontend npm run format` |

> Después de instalar una dependencia de npm, el `package.json` cambia en tu
> máquina (está montado como volumen). **Súbelo al repo** junto con el
> `package-lock.json` para que a los demás les quede la misma versión.

---

## Base de datos

| Qué quiero | Comando |
| --- | --- |
| Consola de PostgreSQL | `./dev.sh psql` |
| Ver en qué puerto quedó | `./dev.sh ports` |
| Listar tablas (dentro de psql) | `\dt` |
| Salir de psql | `\q` |
| Backup a un archivo | `docker compose exec db pg_dump -U el_tapaso el_tapaso > backup.sql` |
| Restaurar un backup | `cat backup.sql \| docker compose exec -T db psql -U el_tapaso -d el_tapaso` |
| Empezar la BD de cero | `./dev.sh clean && ./dev.sh up` |

---

## Sin Docker (no recomendado)

Solo si necesitas correr algo puntual fuera de los contenedores. Requiere tener
Python 3.13, Node 24 y PostgreSQL 18 instalados a mano.

```bash
# Backend
cd apps/backend-django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/local.txt
cp .env.example .env          # cambiar POSTGRES_HOST=localhost
python manage.py migrate
python manage.py runserver

# Frontend
cd apps/frontend-react
npm install
cp .env.example .env
npm run dev
```

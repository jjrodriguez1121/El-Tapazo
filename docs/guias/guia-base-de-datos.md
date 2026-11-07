# Guía de base de datos

El proyecto funciona con PostgreSQL en dos modos, y se cambia de uno a otro con
**una sola variable** del `.env`. Django no nota la diferencia: para él siempre
es "un Postgres en tal dirección".

| Modo | `COMPOSE_PROFILES` | Dónde vive la base de datos |
| --- | --- | --- |
| **Local** (por defecto) | `local-db` | Contenedor `tapaso_db` en tu máquina |
| **Remoto** (Supabase) | *(vacío)* | Servidores de Supabase |

---

## Modo local

Es el de por defecto y no requiere internet. Cada quien tiene su propia copia de
los datos y puede romperla sin afectar a nadie:

```bash
./dev.sh up
```

Para empezar de cero: `./dev.sh clean && ./dev.sh up`.

---

## Modo Supabase

### 1. Obtener los datos de conexión

En el panel de Supabase: **Settings → Database → Connection string**, y elige la
pestaña **Session pooler**. Verás algo así:

```
postgresql://postgres.abcdefghijklmno:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
             └────────── usuario ──────────┘         └──────────── host ────────────────┘ └puerto┘ └─BD─┘
```

> **Usa el *Session pooler*, no la conexión directa.** La directa
> (`db.xxx.supabase.co`) solo resuelve por IPv6 y muchas redes domésticas no lo
> soportan. Y usa el puerto **5432**, no el 6543: el 6543 es *transaction mode*
> y rompe las *prepared statements* de psycopg y el `CONN_MAX_AGE` que tenemos
> configurado.

### 2. Rellenar el `.env`

```env
COMPOSE_PROFILES=

POSTGRES_HOST=aws-1-us-east-2.pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_USER=postgres.abcdefghijklmno
POSTGRES_PASSWORD=tu-contraseña
POSTGRES_DB=postgres
```

`COMPOSE_PROFILES` vacío hace que el contenedor de PostgreSQL **no se levante**:
ya no hace falta.

### 3. Levantar

```bash
./dev.sh up
```

Las migraciones se aplican solas contra Supabase al arrancar el backend. Puedes
comprobar que las tablas quedaron creadas en el panel: **Table Editor**.

### 4. Volver al modo local

Pon `COMPOSE_PROFILES=local-db` y comenta las cuatro líneas de Supabase.

---

## Reglas al trabajar con Supabase

**1. El esquema lo manda Django, siempre.**
Las tablas se crean y modifican con `./dev.sh makemigrations` y `./dev.sh migrate`.
**Nunca** crees ni edites tablas desde el Table Editor de Supabase: las
migraciones se desincronizan y arreglarlo después es un dolor de cabeza.

Por lo mismo, **no conectes el repositorio de GitHub con Supabase**: esa
integración existe para que Supabase administre el esquema desde archivos SQL, y
chocaría de frente con las migraciones de Django. Una sola herramienta manda
sobre el esquema.

**2. Cuidado con el N+1.**
Cada consulta viaja por internet (~50-150 ms, contra ~1 ms en local). Un listado
que dispara 100 consultas pasa de 100 ms a 10 segundos. Usa `select_related` y
`prefetch_related` — ver [reglas de base de datos](../../varios/reglas/reglas-base-de-datos.md).

**3. La contraseña no se sube a git.**
Vive solo en tu `.env` y en tu gestor de contraseñas. Si se filtra, se rota
desde el panel de Supabase.

**4. El plan gratuito se pausa.**
500 MB y **el proyecto se apaga tras 7 días sin consultas**. Si un día no
conecta, entra al panel y reactívalo.

---

## Comandos útiles

| Qué quiero | Comando |
| --- | --- |
| Aplicar migraciones | `./dev.sh migrate` |
| Crear migraciones | `./dev.sh makemigrations` |
| Ver el SQL de una migración | `./dev.sh manage sqlmigrate usuarios 0001` |
| Consola psql (**solo modo local**) | `./dev.sh psql` |
| Ver el estado de las migraciones | `./dev.sh manage showmigrations` |
| Crear el staff de plataforma | `./dev.sh superuser` |

---

## Pendiente: Row Level Security

El diseño original contempla aislamiento por negocio con RLS de PostgreSQL. Está
**pendiente de implementar** y hay dos decisiones abiertas:

1. El usuario `postgres` de Supabase es dueño de las tablas y **se salta RLS por
   diseño**. Para que las políticas sirvan, la aplicación tiene que conectarse
   con un rol de menor privilegio (`app_user`), distinto del que ejecuta las
   migraciones.
2. La variable `app.current_negocio_id` se fija con `SET LOCAL`, que solo vive
   dentro de una transacción: hará falta `ATOMIC_REQUESTS` o un middleware que
   abra la transacción. Con `SET` a secas y conexiones persistentes, el negocio
   de un usuario se filtraría a la petición de otro.

Mientras tanto, el aislamiento se hace en la capa de `repositorios/`, filtrando
siempre por el negocio del usuario autenticado.

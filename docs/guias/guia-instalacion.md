# Guía de instalación

De cero hasta tener el proyecto corriendo. **No necesitas instalar Python, Node
ni PostgreSQL en tu computador**: todo corre dentro de contenedores, así que
todos usamos exactamente las mismas versiones.

---

## 1. Requisitos

Lo único que hay que tener instalado:

| Herramienta | Versión mínima | Cómo verificar |
| --- | --- | --- |
| Git | 2.30+ | `git --version` |
| Docker Engine | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |

> **Windows / macOS:** instalar [Docker Desktop](https://www.docker.com/products/docker-desktop/),
> que ya trae Docker Engine y Compose.
>
> **Linux:** instalar Docker Engine y el plugin `docker-compose-v2`. Después,
> para no tener que escribir `sudo` en cada comando:
> ```bash
> sudo usermod -aG docker $USER   # y cerrar sesión / reiniciar
> ```

El script `./dev.sh` solo necesita bash (en Windows: Git Bash o WSL).

---

## 2. Clonar el repositorio

```bash
git clone <url-del-repo>
cd El-Tapaso
```

---

## 3. Levantar todo con `dev.sh`

```bash
./dev.sh up --build
```

Eso es todo. El script se encarga de:

1. Crear tu archivo `.env` a partir de `.env.example` (guarda claves y puertos;
   **no se sube a git**, cada quien tiene el suyo).
2. **Buscar puertos libres.** Si el 5432 ya lo usa un PostgreSQL instalado en tu
   máquina, o el 8000 lo usa otro proyecto, toma el siguiente disponible, te
   avisa y lo guarda en el `.env` para las próximas veces.
3. Levantar los tres contenedores y esperar a que respondan.
4. Imprimir las URLs que te quedaron.

La primera vez se demora varios minutos: descarga las imágenes, instala las
dependencias de Python y de Node, y crea la base de datos. Después arranca en
segundos con `./dev.sh up`.

Al terminar verás algo así:

```
  ! Puerto 8000 ocupado -> backend en 8001
  ✓ Puertos: base de datos 5434 · backend 8001 · frontend 5173

El Tapaso está arriba:

  Frontend .............. http://localhost:5173
  API ................... http://localhost:8001/api/v1/
  Documentación API ..... http://localhost:8001/api/docs/
  Admin de Django ....... http://localhost:8001/admin/
  PostgreSQL ............ localhost:5434
```

Las migraciones se aplican solas al arrancar el backend.

> **Windows:** el script necesita bash. Úsalo desde **Git Bash** o **WSL**. Si
> prefieres no usarlo, `docker compose up --build` funciona igual, pero los
> puertos los tienes que resolver a mano en el `.env`.

### Comandos del script

| Comando | Qué hace |
| --- | --- |
| `./dev.sh up` | Levanta todo |
| `./dev.sh up --build` | Levanta reconstruyendo las imágenes |
| `./dev.sh up backend` | Levanta solo un servicio (`db`, `backend` o `frontend`) |
| `./dev.sh down` | Apaga (los datos de la base se conservan) |
| `./dev.sh restart` | Apaga y vuelve a levantar |
| `./dev.sh status` | Estado de los servicios y sus URLs |
| `./dev.sh logs` | Logs en vivo (`./dev.sh logs backend` para uno solo) |
| `./dev.sh ports` | Muestra qué puertos te quedaron asignados |
| `./dev.sh clean` | Borra contenedores **y base de datos** (pide confirmación) |
| `./dev.sh help` | Lista todo lo anterior |

---

## 4. Crear el usuario administrador

En **otra terminal**, con los contenedores corriendo:

```bash
docker compose exec backend python manage.py createsuperuser
```

Con ese usuario entras a http://localhost:8000/admin/.

Ese es el **staff de la plataforma**: no pertenece a ningún negocio, y es
quien los da de alta. Para poder usar la aplicación de verdad hace falta un
negocio y su primer administrador:

```bash
# 1. Crea el negocio en http://localhost:8000/admin/negocios/negocio/
# 2. Invita a su administrador (el id del negocio sale de la URL del admin):
./dev.sh manage invitar_administrador --negocio 1 --correo ana@bar.com
```

Le llega un correo con un enlace para que **elija su propia contraseña**. A
partir de ahí, ese administrador invita a su equipo desde la aplicación: no
hay registro público, y nadie más vuelve a necesitar el superusuario.

---

## 5. El correo en desarrollo

El sistema manda tres correos: la invitación, la recuperación de contraseña y
la verificación del correo.

**No tienes que configurar nada.** En desarrollo ninguno sale a internet: todos
caen en una bandeja de entrada de mentira que corre en tu máquina.

```bash
./dev.sh correos
```

Se abre en <http://localhost:8025> y ahí está el correo con su enlace clicable.
La bandeja se levanta sola con `./dev.sh up`, es un contenedor más.

Cómo disparar cada correo y qué comprobar está en la
[guía para probar los correos](guia-probar-los-correos.md).

### Si necesitas enviarlos de verdad

Solo hace falta para probar la entrega real. Consigue credenciales SMTP —Brevo
da 300 correos al día gratis; Resend, 3.000 al mes— y ponlas en tu `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.sendinblue.com
EMAIL_PORT=587
EMAIL_HOST_USER=...        # el "Iniciar sesión" que muestra el panel
EMAIL_HOST_PASSWORD=...    # la clave SMTP
DEFAULT_FROM_EMAIL=El Tapaso <un-remitente-validado@ejemplo.com>
```

Tres avisos que ahorran media tarde:

- **El host de Brevo no es el que dice su panel.** El panel muestra
  `smtp-relay.brevo.com`, pero el nodo que atiende Sudamérica presenta un
  certificado emitido solo para `smtp-relay.sendinblue.com` —el nombre
  viejo—, así que con el nuevo la conexión falla con
  `CERTIFICATE_VERIFY_FAILED: Hostname mismatch`. Es el mismo servidor y la
  misma clave: usa `smtp-relay.sendinblue.com`.
- El `DEFAULT_FROM_EMAIL` tiene que ser un remitente **validado** en el panel
  del proveedor. Si no lo está, rechaza el envío aunque las credenciales sean
  correctas.
- La clave SMTP es un secreto. Vive en tu `.env` y en tu gestor de
  contraseñas: nunca en git ni en el chat del grupo.

Todas estas variables están documentadas en `.env.example`.

---

## 6. Levantar solo una parte

No siempre hace falta levantar todo.

```bash
./dev.sh up backend    # solo backend (arrastra la base de datos: depende de ella)
./dev.sh up frontend   # solo frontend
./dev.sh up db         # solo la base de datos
```

---

## 7. Apagar

```bash
./dev.sh down     # detiene y borra los contenedores (la BD se conserva)
./dev.sh clean    # además borra el volumen: SE PIERDEN LOS DATOS
```

---

## 8. Verificar que quedó bien

```bash
./dev.sh status
```

Los tres servicios deben salir en `Up` y la base de datos como `(healthy)`.
Luego abre en el navegador la URL del frontend que imprime el script: debe
aparecer la pantalla de iniciar sesión.

---

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `port is already allocated` | Ese puerto ya lo usa otro programa | Usa `./dev.sh up`: reasigna solo. A mano: cambia `BACKEND_PORT`, `FRONTEND_PORT` o `POSTGRES_PORT_HOST` en tu `.env` |
| `permission denied ... docker.sock` | Tu usuario no está en el grupo docker | `sudo usermod -aG docker $USER` y reinicia sesión |
| El backend no conecta a la base de datos | La BD todavía arrancaba | `./dev.sh restart` |
| Alguien agregó una dependencia de Python y no aparece | La imagen del backend quedó vieja | `./dev.sh up --build`. Las del frontend no hace falta: se instalan solas al levantar |
| (Windows) Se repite "no se encontró Python... Microsoft Store" al buscar puertos | El `python3` que trae Windows es un acceso directo a la Store, no Python | Ya está resuelto en `dev.sh`: actualiza la rama. Si aún lo ves, desactiva el alias en *Configuración > Aplicaciones > Alias de ejecución de aplicaciones* |
| (Windows) `$'\r': command not found` al correr `./dev.sh` | El repo se clonó con finales de línea CRLF | `git config --global core.autocrlf input`, luego `git rm --cached -r .` y `git reset --hard` dentro del proyecto |
| (Windows) `exec /usr/local/bin/entrypoint.sh: no such file or directory` | Lo mismo: CRLF dentro del contenedor | Igual que la fila anterior, y después `./dev.sh up --build` |
| El frontend no recarga los cambios (Windows/WSL) | El watcher no ve el sistema de archivos | Descomenta `usePolling: true` en `apps/frontend-react/vite.config.js` |

Más detalle en la [guía de Docker](guia-docker.md).

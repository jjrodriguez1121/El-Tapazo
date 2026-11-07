# Guía: probar los correos

El sistema manda tres correos —la **invitación**, la **recuperación de
contraseña** y la **verificación del correo**—, y los tres llevan un enlace con
un token dentro.

En desarrollo **no se envía ninguno de verdad**: todos caen en una bandeja de
entrada de mentira que corre en tu máquina. No hace falta ninguna credencial,
no gasta cupo de ningún proveedor y funciona sin internet.

```bash
./dev.sh correos
```

Eso abre <http://localhost:8025>. Ahí está todo el correo que manda el backend,
con su asunto, su destinatario y **el enlace clicable**.

---

El circuito real es este:

1. El usuario escribe su correo en "olvidé mi contraseña"  →  POST a la API  →  202
2. En la pestaña de la bandeja aparece el correo, solo, sin recargar
3. HACE CLIC en el enlace del correo
        ↓
4. El navegador abre  localhost:5173/nueva-contrasena?uid=Mg&token=dee4p4-...
        ↓
5. Esa pantalla del frontend lee uid y token de la URL (useSearchParams),
   los mete en el formulario de "contraseña nueva" y hace
   POST /contrasena/restablecimiento/  con  {uid, token, contrasena}
        ↓
6. 204  →  a iniciar sesión

---

## Índice

1. [Cómo se prueba un flujo, de principio a fin](#1-cómo-se-prueba-un-flujo-de-principio-a-fin)
2. [Cómo disparar cada correo](#2-cómo-disparar-cada-correo)
3. [Probar el token a mano, sin el navegador](#3-probar-el-token-a-mano-sin-el-navegador)
4. [Las cuatro comprobaciones que importan](#4-las-cuatro-comprobaciones-que-importan)
5. [Problemas frecuentes](#5-problemas-frecuentes)
6. [Si de verdad necesitas enviar correos](#6-si-de-verdad-necesitas-enviar-correos)

---

# 1. Cómo se prueba un flujo, de principio a fin

Con la bandeja abierta al lado, son tres pasos:

1. **Abre la bandeja:** `./dev.sh correos`
2. **Dispara la acción** en la aplicación (invitar a alguien, pedir recuperar
   la contraseña…). El correo aparece **solo**, sin recargar.
3. **Haz clic en el enlace** del correo. Te lleva al frontend, que lee el token
   y llama a la API.

Eso es todo. No hay que leer logs ni copiar nada a mano.

La bandeja además te deja ver la versión en texto y la versión HTML, revisar
las cabeceras y borrar todo con un botón para empezar limpio.

> **La bandeja se levanta sola** con `./dev.sh up`, junto al backend y el
> frontend. Es un contenedor más (`tapaso_mailpit`), y `./dev.sh status` te dice
> en qué puerto quedó si el 8025 estaba ocupado.

---

# 2. Cómo disparar cada correo

Los ejemplos usan el puerto **8000**, el de `.env.example`. Si `./dev.sh up` te
asignó otro, usa el tuyo (`./dev.sh ports` te lo dice).

## Invitación

Es el correo con el que nace toda cuenta: **no hay registro público**.

Al **primer administrador de un negocio** lo invita el staff desde la terminal.
El `--negocio` es el id que ves en la URL del admin de Django:

```bash
./dev.sh manage invitar_administrador --negocio 1 --correo ana@bar.com
```

A **los demás** los invita ese administrador desde la aplicación, o con la API:

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/invitaciones/ \
  -H "Authorization: Bearer <tu-acceso>" \
  -H "Content-Type: application/json" \
  -d '{"correo": "luis@bar.com", "rol": "mesero"}'
```

## Recuperación de contraseña

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/contrasena/recuperacion/ \
  -H "Content-Type: application/json" \
  -d '{"correo": "maria@bar.com"}'
```

Responde **202** siempre, exista o no ese correo. No es un descuido: si
contestara distinto, cualquiera podría averiguar quién tiene cuenta probando
correos uno por uno. Para saber si de verdad salió, mira la bandeja.

## Verificación del correo

Casi nunca hace falta: **quien acepta una invitación ya llega verificado**,
porque para aceptarla tuvo que abrir el enlace que le llegó. Este flujo es para
las cuentas creadas a mano desde el admin de Django.

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/verificacion-correo/solicitud/ \
  -H "Content-Type: application/json" \
  -d '{"correo": "maria@bar.com"}'
```

También responde **202** siempre, por lo mismo.

---

# 3. Probar el token a mano, sin el navegador

Lo normal es hacer clic en el enlace: las pantallas `/invitacion`,
`/nueva-contrasena` y `/verificar-correo` ya existen y hacen todo solas. Si
quieres probar solo el backend, llama a la API a mano: copia el enlace desde la
bandeja y saca los parámetros.

## Aceptar una invitación

El enlace trae un solo parámetro, `token`:

```
http://localhost:5173/invitacion?token=B8jVsIRrpRsHErt2SloHrXbc1Gp5ziVL...
```

Primero, ver de qué es (esto es lo que la pantalla usará para decir "te
invitaron a X como mesero"):

```bash
curl "http://localhost:8000/api/v1/usuarios/invitaciones/pendiente/?token=B8jVsIRrpRsHErt2..."
```

```json
{"correo":"luis@bar.com","rol":"mesero","negocio":"Bar El Tapaso","expira_en":"..."}
```

Y aceptarla:

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/invitaciones/aceptacion/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "B8jVsIRrpRsHErt2...",
    "nombre": "Luis",
    "apellido": "Pérez",
    "telefono": "3001234567",
    "contrasena": "Bar.Tapaso.2026"
  }'
```

**201**, y devuelve la sesión ya abierta: `acceso`, `refresco` y el `usuario`.
No hay que volver a iniciar sesión.

## Restablecer la contraseña

Este enlace trae **dos** parámetros, `uid` y `token`:

```
http://localhost:5173/nueva-contrasena?uid=Mg&token=dee4p4-3781ec3bca94...
```

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/contrasena/restablecimiento/ \
  -H "Content-Type: application/json" \
  -d '{"uid": "Mg", "token": "dee4p4-3781ec3bca94...", "contrasena": "Nueva.Clave.Tapaso.2026"}'
```

**204**, y a iniciar sesión con la nueva.

## Verificar el correo

Igual, `uid` y `token`:

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/verificacion-correo/confirmacion/ \
  -H "Content-Type: application/json" \
  -d '{"uid": "Mg", "token": "dee4q2-3792fc5377..."}'
```

**204**, y a partir de ahí esa cuenta ya puede iniciar sesión.

---

# 4. Las cuatro comprobaciones que importan

Si vas a dar por bueno el flujo, comprueba estas cuatro cosas. Las tres
primeras se rompen en silencio.

**1. El enlace está entero.** Tiene que verse `&token=`, nunca `&amp;token=`.
Si sale escapado, el frontend leería un parámetro llamado `amp;token` y nunca
encontraría el token. (Pasó una vez; hay una prueba que lo vigila.)

**2. El enlace sirve UNA sola vez.** Usa el mismo dos veces seguidas: la
segunda tiene que fallar con `HTTP 400` y

```json
{"error":{"codigo":"enlace_invalido","mensaje":"El enlace no es válido o ya venció. Solicita uno nuevo."}}
```

Si la segunda vez funciona, hay un problema serio.

**3. Un token no sirve para otra cosa.** El de recuperación no verifica el
correo, y al revés: tienen firma distinta. Los dos casos dan `enlace_invalido`.

**4. El rol lo pone quien invita.** Manda `"rol": "admin"` en el cuerpo de
`invitaciones/aceptacion/` y comprueba que el usuario creado **no** es
administrador: ese campo se ignora, viene de la invitación. Si alguien pudiera
elegir su propio rol, cualquier invitado se haría administrador.

---

# 5. Problemas frecuentes

| Lo que ves | Qué pasa |
| --- | --- |
| La bandeja no abre en `localhost:8025` | El puerto estaba ocupado y `./dev.sh up` asignó otro. Míralo con `./dev.sh correos` o `./dev.sh status` |
| La bandeja está vacía | El contenedor `tapaso_mailpit` no está arriba (`./dev.sh status`), o tu `.env` tiene credenciales SMTP de verdad y el correo salió a internet. Ver [§6](#6-si-de-verdad-necesitas-enviar-correos) |
| La recuperación responde 202 y no llega nada | Ese correo no tiene cuenta, o está desactivada. Responde 202 igual, a propósito |
| `enlace_invalido` la primera vez | Copiaste el enlace cortado. Ojo: `uid` y `token` son **dos** parámetros separados por `&` |
| `correo_no_verificado` al iniciar sesión | La cuenta existe y la contraseña está bien, pero falta abrir el enlace de verificación. Ver [§2](#2-cómo-disparar-cada-correo) |
| `demasiadas_peticiones` (429) | El freno contra fuerza bruta: 10 intentos de acceso por minuto y 5 correos por hora, por IP. Espera un rato |
| `invitacion_pendiente_duplicada` | Ya hay una invitación sin usar para ese correo. Cancélala o reenvíala desde la aplicación |

## Si prefieres no usar la bandeja

Se puede volver a la salida por consola, donde el correo se imprime como texto.
En tu `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Y entonces el correo aparece en los logs… **con una trampa**: sale en los logs
del servidor si lo disparó una petición HTTP, pero en la salida del propio
comando si lo lanzaste con `./dev.sh manage`, porque ese es otro proceso.

```bash
./dev.sh logs backend                          # en vivo (Ctrl+C para salir)
docker compose logs backend --tail 80          # lo que ya pasó
```

Justamente por esa trampa existe la bandeja.

---

# 6. Si de verdad necesitas enviar correos

Solo hace falta para comprobar la entrega real: que llegue a la bandeja de
entrada de alguien y no a la carpeta de spam. Para todo lo demás, Mailpit
alcanza y sobra.

Dos avisos antes de pedir la clave del proyecto:

- **El cupo es compartido.** Todas las claves SMTP de una misma cuenta comen del
  mismo plato: 300 correos al día entre todos. Si alguien prueba en bucle, se
  acaban para el resto.
- **Es más limpio tener la tuya.** Una cuenta gratuita de Brevo son 300 correos
  diarios propios y tu propio remitente. Si dejas el proyecto, no hay nada que
  revocar.

Los pasos y el `.env` están en la
[guía de instalación, §5](guia-instalacion.md#5-el-correo-en-desarrollo),
incluido el detalle del host de Brevo que no coincide con lo que dice su panel.

En cuanto pongas credenciales SMTP en tu `.env`, el correo **deja de llegar a la
bandeja** y sale a internet de verdad. Coméntalas para volver.

---

## Referencias

- [Guía de instalación](guia-instalacion.md) — levantar el proyecto y configurar el `.env`
- [Conectarse a la API](guia-api-autenticacion.md) — todos los endpoints, con ejemplos y códigos de error
- <http://localhost:8000/api/docs/> — el contrato, generado por el propio código

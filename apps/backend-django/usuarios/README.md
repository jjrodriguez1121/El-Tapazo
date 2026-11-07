# App: `usuarios`

Identidad y acceso: quién es cada persona, en qué negocio trabaja y con qué rol. Los **clientes no viven aquí** — no se registran ni tienen contraseña.

**Modelos:** `Usuario` (con credenciales), `Invitacion` (alta de trabajadores por correo).

## Cómo entra la gente

**No hay registro público.** Si lo hubiera, cualquiera podría darse de alta en
un negocio ajeno. Las cuentas nacen de una invitación:

```
./dev.sh manage invitar_administrador --negocio 1 --correo ana@bar.com
        │  (staff de la plataforma, una vez por negocio)
        ▼
El administrador abre el enlace, elige su contraseña y entra
        ▼
Desde la aplicación invita a sus meseros y cajeros
```

Quien acepta una invitación **nace con el correo verificado**: para aceptarla
tuvo que abrir el enlace que llegó a ese correo, que es justo lo que la
verificación comprueba. Sin verificar, el inicio de sesión responde `403`.

## Sesión

JWT con `djangorestframework-simplejwt`: un `acceso` de 15 minutos y un
`refresco` de 7 días que **rota** en cada renovación. Cerrar sesión anula el
refresco de verdad (tablas `token_blacklist_*`), porque en un bar los
dispositivos se comparten.

## Los tres tipos de token, y por qué no son el mismo

| Para qué | Dónde vive | Qué lo invalida |
| --- | --- | --- |
| Invitación | `invitaciones.hash_token` (solo el hash) | Aceptarla, revocarla o reenviarla |
| Recuperar contraseña | En ningún sitio: va firmado | Cambiar la contraseña, o 24 h |
| Verificar correo | En ningún sitio: va firmado | Verificar el correo, o 24 h |

Los dos últimos no necesitan tabla porque llevan dentro el estado que los mata.
Ver `tokens.py`.

## Contrato con el frontend

[`docs/guias/guia-api-autenticacion.md`](../../../docs/guias/guia-api-autenticacion.md)
— endpoints, ejemplos y códigos de error. Y `/api/docs/`, que lo genera el
propio código.

## Carpetas

| Carpeta | Qué va aquí |
| --- | --- |
| `api/` | Vistas, serializers y routers (capa HTTP). |
| `dtos/` | Objetos de transferencia de datos entre capas (dataclasses). |
| `excepciones/` | Excepciones propias del dominio de esta app. |
| `management/` | Comandos de terminal (`invitar_administrador`). |
| `migrations/` | Migraciones de base de datos (nombre exigido por Django). |
| `permisos/` | Permisos de DRF específicos de esta app. |
| `repositorios/` | Acceso a datos: consultas al ORM aisladas del resto. |
| `selectores/` | Lecturas / consultas de negocio. |
| `servicios/` | Reglas de negocio y escrituras. |
| `pruebas/` | Pruebas de esta app. |
| `validadores/` | Validaciones reutilizables del dominio. |
| `tokens.py` | Generación y comprobación de los tokens de los enlaces. |

Reglas de código: [`varios/reglas/`](../../../varios/reglas/README.md) ·
Arquitectura: [`docs/backend/estructura.md`](../../../docs/backend/estructura.md)

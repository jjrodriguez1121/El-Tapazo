# Estructura del backend

Qué va exactamente en cada carpeta de `apps/backend-django/`.

---

## Vista general

```
apps/backend-django/
├── config/                 Configuración del proyecto Django (no es una app)
│   ├── settings/
│   │   ├── base.py         Configuración común a todos los entornos
│   │   ├── local.py        Desarrollo
│   │   ├── production.py   Producción
│   │   └── test.py         Pruebas
│   ├── urls.py             Mapa de URLs raíz
│   ├── wsgi.py             Punto de entrada para gunicorn
│   └── asgi.py             Punto de entrada asíncrono
│
├── nucleo/                 Código compartido entre todas las apps
├── negocios/               Negocios (la raíz: todo cuelga de aquí)
├── usuarios/               Quien opera el sistema, roles e invitaciones
├── clientes/               Quien compra en el bar: la ficha de la persona
├── catalogo/               Productos y precios
├── inventario/             Ubicaciones, existencias y kardex de movimientos
├── eventos/                Canal evento/bar: pulseras NFC, cuentas, comandas y pagos
├── distribucion/           Canal mayorista: tiendas cliente y sus pedidos
│
├── requirements/           Dependencias por entorno
├── scripts/                Scripts del contenedor (entrypoint)
├── static/                 Archivos estáticos propios del backend
├── media/                  Archivos subidos por los usuarios
├── templates/              Plantillas HTML (correos, admin)
├── locale/                 Traducciones
├── manage.py               Comandos de Django
├── pyproject.toml          Configuración de ruff, pytest y coverage
└── Dockerfile
```

Cada app de dominio es un **módulo del negocio**, y todas tienen la misma
estructura interna por dentro. Así, si sabes moverte en una, sabes moverte en
todas.

---

## Anatomía de una app

```
catalogo/
├── api/            Capa HTTP: vistas, serializers, routers
├── dtos/           Objetos de transferencia de datos entre capas
├── excepciones/    Errores propios del dominio
├── migrations/     Migraciones de base de datos (nombre exigido por Django)
├── permisos/       Permisos de DRF de esta app
├── repositorios/   Acceso a datos: consultas al ORM
├── selectores/     Consultas de negocio (lectura)
├── servicios/      Reglas de negocio (escritura)
├── pruebas/        Pruebas
├── validadores/    Validaciones reutilizables
├── __init__.py
├── admin.py        Registro en el panel de administración
├── apps.py         Configuración de la app
├── models.py       Tablas de la base de datos
├── urls.py         Rutas de la app
└── README.md       Para qué sirve esta app
```

> `models.py`, `admin.py`, `apps.py` y `migrations/` conservan su nombre en
> inglés porque Django los busca exactamente así. Todo lo demás va en español.

---

## Cómo fluye una petición

```
Petición HTTP
     │
     ▼
 urls.py ──> api/vistas.py ──> api/serializers.py  (¿los datos llegan bien?)
     │                              │
     │                              ▼
     │                       validadores/          (¿son válidos para el negocio?)
     │                              │
     │              ┌───────────────┴───────────────┐
     │              ▼                               ▼
     │       selectores/  (leer)           servicios/  (escribir)
     │              │                               │
     │              └───────────────┬───────────────┘
     │                              ▼
     │                       repositorios/          (hablar con el ORM)
     │                              │
     │                              ▼
     │                          models.py           (tablas)
     ▼
Respuesta JSON
```

**Regla de oro:** la vista no toma decisiones de negocio. Recibe, delega y
responde.

---

## Carpeta por carpeta

### `api/` — la capa HTTP

Todo lo que tiene que ver con HTTP y con el formato de entrada/salida.

- `vistas.py` (o `viewsets.py`) — recibe la petición, llama a un *service* o a un
  *selector*, devuelve la respuesta. Debe ser corto.
- `serializers.py` — convierte JSON ↔ objetos de Python y valida el **formato**
  de los datos (tipos, campos obligatorios, longitudes).
- `routers.py` / `urls.py` — arma las rutas de la app.
- `filtros.py` — filtros de `django-filter` para los listados.

No va aquí: reglas de negocio, consultas complejas al ORM.

### `servicios/` — las reglas de negocio (escritura)

Una función por caso de uso. Reciben datos ya validados, ejecutan la regla y
guardan. Son el corazón del sistema: aquí vive lo que hace el negocio, no en la
vista ni en el modelo.

Ejemplos para este proyecto: `registrar_entrada_de_mercancia`,
`transferir_entre_ubicaciones`, `ajustar_existencias`.

Reglas: una función = una acción; reciben tipos simples o DTOs, no objetos
`request`; si tocan varias tablas, van dentro de una transacción.

### `selectores/` — las consultas de negocio (lectura)

El espejo de `servicios/` para leer. Devuelven los datos ya preparados para
mostrar: `existencias_por_ubicacion`, `productos_bajo_minimo`.

Separar lectura de escritura evita que un archivo gigante mezcle las dos cosas.

### `repositorios/` — el acceso a datos

Las consultas al ORM aisladas en un solo lugar. Los servicios y los selectores
llaman al repositorio en vez de escribir `Modelo.objects.filter(...)` regados por
todo el código.

Ventaja: si cambia una consulta o hay que optimizarla, se toca un solo archivo,
y las pruebas pueden reemplazar el repositorio por uno falso.

Regla que hace que esto se sostenga: **`Modelo.objects` solo aparece dentro de
`repositorios/`**. Si aparece en un servicio, en un selector o en una vista, es
que falta una función de repositorio.

### `dtos/` — objetos de transferencia

`dataclasses` congeladas (`@dataclass(frozen=True)`, sufijo `DTO`) que llevan
datos entre capas sin arrastrar objetos de Django.
Sirven para que un *service* reciba un paquete de datos claro y tipado en vez de
un diccionario suelto.

### `validadores/` — validaciones reutilizables

Funciones que verifican reglas del dominio: que un SKU tenga el formato
acordado, que una cantidad no sea negativa, que un NIT sea válido. Se usan desde
los serializers, los modelos o los servicios.

Diferencia con el serializer: el serializer valida **forma** (es un entero, no
está vacío); el validator valida **negocio** (ese código ya existe, esa cantidad
supera el stock).

### `permisos/` — quién puede hacer qué

Clases de permisos de DRF **propias de la app**, cuando una regla solo tiene
sentido ahí. Las que usan dos o más apps —`EsAdministrador`,
`EsCajeroOAdministrador`, `EsDelEquipo`— viven en `nucleo/permisos/`.

### `excepciones/` — errores del dominio

Excepciones propias (`ExistenciasInsuficientes`, `ProductoDuplicado`) que los
servicios lanzan y que el manejador global de `nucleo/excepciones/` traduce a una
respuesta HTTP con su código correspondiente. Así el negocio no sabe nada de HTTP.

Todas heredan de `ErrorDeNegocio` y sobrescriben `mensaje`, `codigo` y
`status_http`.

### `migrations/` — historial de la base de datos

Las genera Django con `makemigrations`. **Se suben a git** y no se editan a
mano salvo casos puntuales (migraciones de datos).

### `pruebas/` — pruebas

Un archivo por capa: `test_servicios.py`, `test_selectores.py`, `test_api.py`,
`test_modelos.py`, más `fabricas.py` con los datos de prueba. Ver
[convenciones.md](convenciones.md).

### `models.py` — las tablas

Solo la definición de datos: campos, relaciones, `Meta`, `__str__`, propiedades
calculadas simples. Las reglas de negocio con varios pasos van en `servicios/`,
no en el modelo.

Si una app llega a tener muchos modelos, `models.py` puede volverse la carpeta
`models/` con un archivo por modelo y un `__init__.py` que los reexporte.

### `admin.py` — panel de administración

Registro de los modelos para el admin de Django. Muy útil para cargar datos de
prueba.

### `urls.py` — rutas de la app

Se incluye desde `config/urls.py` bajo `/api/v1/<app>/`.

---

## `nucleo/` — lo compartido

Lo que usan todas las apps y no pertenece a ningún dominio:

| Carpeta | Contenido |
| --- | --- |
| `models.py` | Modelos abstractos base: `ModeloConFechas` (`creado_en`/`actualizado_en`) y `ModeloDelNegocio`, del que hereda todo lo que cuelga de un negocio. |
| `api/` | Vistas y serializers base, y `MixinDelNegocio`: el único sitio del que sale el `negocio_id` del usuario autenticado. |
| `excepciones/` | `ErrorDeNegocio`, los errores comunes a varias apps y el manejador global de DRF. |
| `permisos/` | Permisos por rol que usan todas las apps: `EsAdministrador`, `EsCajeroOAdministrador`, `EsDelEquipo`. |
| `paginacion/` | Clases de paginación compartidas. |
| `middleware/` | Middlewares propios. |
| `utilidades/` | Utilidades genéricas (fechas, formatos). |

Si algo se usa en dos apps o más, probablemente va en `nucleo/`.

---

## `config/` — la configuración

No es una app: es el proyecto. La configuración está partida por entorno para
que desarrollo y producción no compartan valores peligrosos:

- `base.py` — todo lo común. Lee las variables sensibles del entorno.
- `local.py` — `DEBUG = True`, correo por consola, CORS abierto.
- `production.py` — `DEBUG = False`, HTTPS forzado, cookies seguras, whitenoise.
- `test.py` — ajustes para que las pruebas corran rápido.

Cuál se usa lo decide la variable `DJANGO_SETTINGS_MODULE` (la define el
`compose.yaml`).

---

## ¿Dónde pongo mi código? — chuleta

| Lo que quiero hacer | Dónde va |
| --- | --- |
| Definir una tabla nueva | `models.py` |
| Exponer un endpoint | `api/vistas.py` + `urls.py` |
| Convertir un modelo a JSON | `api/serializers.py` |
| "Al registrar una entrada, sumar stock y crear el movimiento" | `servicios/` |
| "Traer los productos por debajo del stock mínimo" | `selectores/` |
| Una consulta al ORM que se repite | `repositorios/` |
| "El SKU debe tener este formato" | `validadores/` |
| "Solo el jefe de bodega puede hacer esto" | `permisos/` |
| "No hay stock suficiente" (error) | `excepciones/` |
| Algo que usan dos o más apps | `nucleo/` |

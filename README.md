# El Tapazo

Aplicación web para administrar las operaciones de un negocio desde un solo
lugar: catálogo, inventario, compras, ventas, cartera, clientes y solicitudes
PQR. El sistema combina una API en Django con una interfaz en React.

## Funcionalidades

| Módulo | Qué permite hacer |
| --- | --- |
| **Acceso** | Iniciar sesión, activar una cuenta mediante invitación, verificar el correo y recuperar la contraseña. |
| **Dashboard** | Consultar ventas y cobros del periodo, cuentas por cobrar y pagar, utilidad bruta, productos más vendidos, entregas pendientes y alertas de stock bajo. |
| **Catálogo e inventario** | Administrar productos, categorías, proveedores e impuestos; consultar existencias y registrar movimientos de inventario. |
| **Compras** | Registrar compras a proveedores, sus productos, descuentos e impuestos; pagar de contado o llevar el saldo a cuentas por pagar. |
| **Punto de venta y ventas** | Crear ventas, aplicar descuentos, seleccionar el medio de pago y consultar el estado de pago y de entrega. |
| **Cartera** | Controlar las cuentas por cobrar y por pagar, fechas de vencimiento, saldos y abonos. |
| **Clientes** | Mantener la ficha del cliente y consultar la información asociada a sus operaciones. |
| **PQR** | Registrar peticiones, quejas, reclamos y sugerencias, asignarlas y conservar su historial de gestión y respuesta. |

El acceso a los módulos y a los datos depende de los permisos del usuario y del
negocio al que pertenece. El negocio no se elige desde la petición de la API.
Las cuentas se habilitan por invitación; no hay registro público de negocios.

## Reglas principales del negocio

- **El inventario se controla con movimientos.** Las ventas requieren productos
  activos y existencias suficientes. Al anular una venta pendiente de entrega,
  se devuelve el inventario mediante movimientos de reverso en vez de borrar el
  historial.
- **El precio de venta lo determina el producto registrado.** La venta conserva
  el precio y los valores de impuesto utilizados al momento de la operación.
- **El precio del punto de venta incluye el IVA.** El impuesto se presenta por
  separado en el detalle, pero no se vuelve a sumar al total cobrado.
- **Ventas de contado y a crédito siguen reglas distintas.** La venta de
  contado necesita un medio de pago activo. La venta a crédito requiere un
  cliente activo y una fecha de vencimiento futura; crea una cuenta por cobrar.
- **Los abonos no pueden exceder el saldo pendiente.** Al anular una venta
  pendiente de entrega, los pagos confirmados asociados se marcan como
  anulados. Los informes solo contabilizan pagos confirmados.
- **Las compras validan sus descuentos.** El descuento de una línea no puede
  superar su valor bruto. Una compra a crédito necesita fecha de vencimiento y
  un total positivo.
- **Los registros históricos se conservan.** Productos, categorías,
  proveedores y clientes se pueden desactivar para evitar nuevas operaciones
  sin perder su relación con compras y ventas anteriores.
- **Las PQR tienen trazabilidad.** Cada solicitud cuenta con radicado, estado y
  seguimientos de gestión; puede relacionarse con un cliente, una venta o una
  compra.

## Alcance actual

La aplicación principal no usa pulseras ni dispositivos NFC. Las tablas de NFC
y `alertas_consumo` se retiraron del esquema mediante migraciones. Tampoco hay
un módulo de campañas de notificaciones implementado; los correos existentes
son transaccionales, por ejemplo, para invitaciones y recuperación de acceso.

El backend conserva código de la aplicación `eventos`, pero sus rutas no están
incluidas en el mapa principal de la API. El flujo de trabajo de la interfaz
documentado arriba es el de los módulos actualmente expuestos.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Backend y API | Python, Django y Django REST Framework |
| Base de datos | PostgreSQL |
| Frontend | React, JavaScript y Vite |
| Desarrollo | Docker Compose |

## Iniciar el proyecto

Requisitos: Git, Docker y Docker Compose. En Windows, ejecuta los comandos de
`dev.sh` desde Git Bash o WSL.

```bash
git clone <url-del-repositorio>
cd El-Tapaso
./dev.sh up --build
```

El script prepara el entorno, elige puertos disponibles y levanta los servicios.
Las migraciones se aplican al iniciar el backend. Las URLs por defecto son:

| Servicio | URL |
| --- | --- |
| Aplicación web | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| Documentación de la API | http://localhost:8000/api/docs/ |
| Administración de Django | http://localhost:8000/admin/ |
| Bandeja de correos de desarrollo | http://localhost:8025 |

Para crear el usuario administrador inicial y habilitar el primer administrador
de un negocio, sigue la [guía de instalación](docs/guias/guia-instalacion.md).
En desarrollo, los correos de invitación, verificación y recuperación se pueden
consultar en la bandeja local de Mailpit.

Comandos frecuentes:

```bash
./dev.sh status     # estado de los servicios y URLs
./dev.sh logs       # logs
./dev.sh down       # apagar sin borrar los datos
./dev.sh help       # comandos disponibles
```

## Pruebas y calidad

Con los contenedores levantados, desde la raíz del repositorio:

```bash
./dev.sh test back       # pruebas del backend
./dev.sh test front      # pruebas del frontend
./dev.sh lint            # linters del backend y frontend
```

La [guía de comandos](docs/guias/guia-comandos.md) incluye comandos para probar
un módulo específico, generar el build del frontend y ejecutar verificaciones
de Django.

## Estructura del repositorio

```text
El-Tapaso/
├── apps/
│   ├── backend-django/    API, modelos y reglas de negocio
│   └── frontend-react/    interfaz web
├── docs/                  guías y convenciones del proyecto
├── docker/                configuración auxiliar de contenedores
├── Logo.png               imagen de marca
├── compose.yaml           entorno de desarrollo
├── compose.prod.yaml      configuración de producción
└── dev.sh                 comandos de desarrollo
```

## Documentación

- [Índice de documentación](docs/README.md)
- [Guía de instalación](docs/guias/guia-instalacion.md)
- [Comandos de desarrollo](docs/guias/guia-comandos.md)
- [Base de datos y Supabase](docs/guias/guia-base-de-datos.md)
- [Entorno Docker](docs/guias/guia-docker.md)
- [Autenticación de la API](docs/guias/guia-api-autenticacion.md)
- [Estructura del backend](docs/backend/estructura.md)
- [Convenciones del backend](docs/backend/convenciones.md)
- [Estructura del frontend](docs/frontend/estructura.md)
- [Convenciones del frontend](docs/frontend/convenciones.md)

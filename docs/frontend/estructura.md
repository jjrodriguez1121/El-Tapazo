# Estructura del frontend

Qué va exactamente en cada carpeta de `apps/frontend-react/`.

La organización es **por módulo de negocio** (*feature-based*): el código de una
misma parte del negocio vive junto, en vez de estar repartido entre carpetas
gigantes de `componentes/`, `hooks/` y `api/`.

---

## Vista general

```
apps/frontend-react/
├── public/                 Archivos servidos tal cual (favicon, robots.txt)
├── src/
│   ├── app/                Arranque de la aplicación
│   │   ├── principal.jsx   Punto de entrada: monta React en el DOM
│   │   ├── Aplicacion.jsx  Componente raíz
│   │   └── proveedores.jsx Proveedores globales (datos, rutas, tema, sesión)
│   │
│   ├── recursos/           Imágenes, iconos y fuentes usadas desde el código
│   │
│   ├── componentes/        Componentes compartidos por toda la app
│   │   ├── ui/             Piezas básicas sin lógica de negocio (Boton, Campo, Modal)
│   │   ├── comunes/        Reutilizables con algo de lógica (Tabla, Buscador)
│   │   └── estructura/     Piezas del armazón visual (Encabezado, Menu, PieDePagina)
│   │
│   ├── configuracion/      Constantes y lectura de variables de entorno
│   │
│   ├── modulos/            EL NÚCLEO: una carpeta por módulo del negocio
│   │   ├── autenticacion/
│   │   ├── tablero/
│   │   ├── catalogo/
│   │   ├── inventario/
│   │   ├── eventos/
│   │   └── distribucion/
│   │
│   ├── hooks/              Hooks reutilizables por toda la app
│   ├── plantillas/         Plantillas de página (con menú, en blanco, de login)
│   ├── librerias/          Configuración de librerías externas (axios, react-query)
│   ├── paginas/            Páginas globales que no son de ningún módulo (404, Inicio)
│   ├── rutas/              Definición de rutas y protección de las privadas
│   ├── estado/             Estado global compartido
│   ├── estilos/            Tailwind y la paleta de colores (globales.css)
│   ├── utilidades/         Funciones auxiliares puras (formatear moneda, fechas)
│   └── pruebas/            Configuración y utilidades de pruebas
│
├── index.html              Plantilla base de Vite
├── vite.config.js          Configuración de Vite (alias @, servidor, pruebas)
├── eslint.config.js        Reglas del linter
├── jsconfig.json           Hace que el editor entienda el alias @
├── package.json            Dependencias y scripts
└── Dockerfile
```

> Se quedan en inglés `src/`, `public/`, `app/`, `hooks/`, `index.html` y los
> archivos de configuración: son nombres que esperan Vite, React o el propio
> ecosistema. `hook` además no tiene traducción usada en la práctica.

---

## Anatomía de un módulo

Cada carpeta de `modulos/` es autocontenida:

```
modulos/catalogo/
├── api/            Llamadas HTTP de este módulo (obtenerProductos, crearProducto)
├── dtos/           Traducen el JSON de la API a objetos de la aplicación, y al revés
├── componentes/    Componentes que solo usa este módulo (FormularioProducto)
├── hooks/          Hooks del módulo (useProductos)
├── paginas/        Pantallas completas (PaginaListaProductos)
├── estado/         Estado local del módulo, si lo necesita
└── utilidades/     Funciones auxiliares del módulo
```

**Regla:** si algo lo usa **un solo** módulo, va dentro de ese módulo. Solo
cuando lo necesita un segundo se sube a `src/componentes/`, `src/hooks/` o
`src/utilidades/`. Así se evita el `componentes/` inmanejable con 80 archivos.

**Regla 2:** un módulo no importa cosas de otro módulo. Si dos necesitan lo
mismo, ese código sube un nivel.

---

## Cómo fluye un dato

```
 Página (modulos/catalogo/paginas/PaginaListaProductos.jsx)
      │  usa
      ▼
 Hook  (modulos/catalogo/hooks/useProductos.js)   ← react-query: caché, carga, errores
      │  llama
      ▼
 API   (modulos/catalogo/api/apiProductos.js)
      │  usa
      ▼
 clienteApi (librerias/clienteApi.js)  ── axios con la URL base y el token
      │
      ▼
 Backend Django  /api/v1/catalogo/productos/
```

El componente no llama a `axios` directamente: llama a un hook. El hook llama a
la capa `api/`. Así, si cambia un endpoint, se toca un solo archivo.

La capa `api/` no devuelve el JSON tal cual: lo pasa por un DTO de `dtos/`
(`productoDesdeApi`, `credencialesHaciaApi`). La API habla en `snake_case` y la
aplicación en `camelCase`; si mañana cambia un campo del contrato, se toca el
DTO y ninguna pantalla se entera.

---

## Carpeta por carpeta

### `app/`

El arranque. `principal.jsx` monta React; `Aplicacion.jsx` es la raíz;
`proveedores.jsx` concentra los proveedores globales (React Query, Router, y más
adelante el de sesión o el de tema). Se toca poco.

### `componentes/ui/`

Piezas de interfaz genéricas y "tontas": `Boton`, `Campo`, `Selector`, `Modal`,
`Cargando`. No saben nada del negocio y no hacen peticiones. Son las que dan
consistencia visual a toda la app.

### `componentes/comunes/`

Reutilizables que sí tienen algo de lógica pero no son de un módulo concreto:
`TablaDatos`, `Buscador`, `Paginacion`, `DialogoConfirmacion`.

### `componentes/estructura/`

`Encabezado`, `MenuLateral`, `PieDePagina`, `Migas`: las piezas con las que se
arman las plantillas.

### `plantillas/`

Plantillas de página completas que combinan lo anterior: `PlantillaPrincipal`
(menú + encabezado, para la app ya autenticada), `PlantillaAcceso` (pantalla
limpia para el login). Las rutas se envuelven con una plantilla.

### `configuracion/`

`entorno.js` es el **único** archivo donde se lee `import.meta.env`. El resto del
código importa `entorno` desde aquí. También van las constantes globales
(estados, roles, tipos de movimiento).

### `librerias/`

Configuración de librerías externas en un solo lugar:

- `clienteApi.js` — instancia de axios con la URL base, las cabeceras y los
  interceptores (agregar el token, manejar el 401).
- `clienteConsultas.js` — configuración de React Query.

### `hooks/`

Hooks generales: `useDebounce`, `useAlmacenamientoLocal`, `useMediaQuery`. Los de
un módulo van en `modulos/<x>/hooks/`.

### `paginas/`

Páginas que no pertenecen a ningún módulo: `PaginaNoEncontrada` y
`PaginaEnConstruccion`, la que ve una sección del menú que todavía no tiene
pantalla. Las páginas de negocio viven en `modulos/<x>/paginas/`; el tablero
de inicio, en `modulos/tablero/`.

### `rutas/`

`index.jsx` define el árbol de rutas. Aquí también va `RutaProtegida`, el
componente que manda al login si no hay sesión.

### `estado/`

Estado global que cruza módulos: sesión del usuario, notificaciones, tema.
**Ojo:** los datos que vienen del servidor no van aquí — de eso se encarga React
Query. El estado global es solo para la interfaz.

### `estilos/`

`globales.css` importa Tailwind y declara en `@theme` todo lo que consume el
resto de la aplicación: **la paleta de colores**, la fuente, los tamaños de texto
y las animaciones del diseño. Es el único sitio donde se escribe un color. Ver
[convenciones](convenciones.md#estilos).

### `utilidades/`

Funciones puras y sin dependencias: `formatearMoneda`, `formatearFecha`,
`calcularTotal`. Fáciles de probar.

### `pruebas/`

`configuracion.js` para Vitest y utilidades compartidas. Las pruebas de cada
componente van al lado del componente (`Boton.test.jsx`).

---

## El alias `@`

`@` apunta a `src/`. Evita los imports frágiles con `../../../`:

```js
import { clienteApi } from '@/librerias/clienteApi'          // ✅
import { clienteApi } from '../../../librerias/clienteApi'   // ❌
```

Está configurado en `vite.config.js` (para el build) y en `jsconfig.json` (para
que el editor lo autocomplete).

---

## ¿Dónde pongo mi código? — chuleta

| Lo que quiero hacer | Dónde va |
| --- | --- |
| Una pantalla nueva de productos | `modulos/catalogo/paginas/` |
| El formulario de esa pantalla | `modulos/catalogo/componentes/` |
| Llamar al endpoint de productos | `modulos/catalogo/api/` |
| Traducir lo que manda o recibe ese endpoint | `modulos/catalogo/dtos/` |
| Traer y cachear esos datos | `modulos/catalogo/hooks/` (con React Query) |
| Un botón que se usa en toda la app | `componentes/ui/` |
| Una tabla reutilizable | `componentes/comunes/` |
| Formatear pesos colombianos | `utilidades/` |
| Guardar el usuario con sesión iniciada | `estado/` |
| Registrar una ruta nueva | `rutas/index.jsx` |
| Un color, tamaño de texto o animación del diseño | `estilos/globales.css`, dentro de `@theme` |

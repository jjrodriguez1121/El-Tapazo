# Convenciones del frontend

---

## Nombres de archivos

| Tipo | Estilo | Ejemplo |
| --- | --- | --- |
| Componentes | `PascalCase.jsx` | `ProductCard.jsx` |
| Hooks | `camelCase` empezando por `use` | `useProducts.js` |
| Utilidades y servicios | `camelCase.js` | `formatCurrency.js`, `productsApi.js` |
| Carpetas | `camelCase` o `kebab-case`, consistente | `modulos/catalogo/` |
| Pruebas | igual que el archivo + `.test.jsx` | `ProductCard.test.jsx` |
| Constantes | `MAYÚSCULAS` dentro del archivo | `MOVEMENT_TYPES` |

Un componente por archivo, y el nombre del archivo igual al del componente.

---

## Componentes

- Siempre funciones, con `export default` para el componente principal.
- Componentes cortos: si pasa de ~150 líneas, hay que partirlo.
- Separar el que **muestra** del que **trae datos**: la página busca los datos,
  el componente los recibe por props y los pinta.
- Nada de lógica de negocio pesada dentro del JSX: sacarla a un hook o a
  `utilidades/`.

```jsx
// TarjetaProducto.jsx
export default function TarjetaProducto({ producto, alSeleccionar }) {
  return (
    <article onClick={() => alSeleccionar(producto.id)}>
      <h3>{producto.nombre}</h3>
    </article>
  )
}
```

---

## Estado

| Tipo de estado | Con qué se maneja |
| --- | --- |
| Estado de un componente | `useState` |
| Estado compartido entre pocos componentes | Levantarlo al padre o `useContext` |
| **Datos del servidor** | **React Query** (`useQuery` / `useMutation`) |
| Estado global de la interfaz (sesión, tema) | `estado/` |

El error más común es guardar en un store la lista de productos que vino de la
API. Eso lo maneja React Query: ya trae caché, `isLoading`, `error` y
revalidación.

---

## Llamadas a la API

- Nunca `axios` ni `fetch` directo dentro de un componente.
- La capa `modulos/<x>/api/` es la única que conoce las URLs.
- Lo que entra y sale pasa por `modulos/<x>/dtos/`: la API habla en
  `snake_case` y la aplicación en `camelCase`, y la traducción vive en un solo
  sitio, un archivo por concepto.
- Los hooks envuelven esas funciones con React Query.
- La URL base sale de `configuracion/entorno.js`, jamás escrita a mano.

```js
// modulos/catalogo/api/apiProductos.js
import { clienteApi } from '@/librerias/clienteApi'

import { productoDesdeApi } from '../dtos/producto'

export const obtenerProductos = (params) =>
  clienteApi
    .get('/catalogo/productos/', { params })
    .then((respuesta) => respuesta.data.results.map(productoDesdeApi))
```

```js
// modulos/catalogo/hooks/useProductos.js
import { useQuery } from '@tanstack/react-query'
import { obtenerProductos } from '../api/apiProductos'

export function useProductos(params) {
  return useQuery({
    queryKey: ['productos', params],
    queryFn: () => obtenerProductos(params),
  })
}
```

---

## Manejo de estados de carga y error

Toda vista que trae datos debe contemplar los tres casos: cargando, error y
vacío. Una tabla sin el mensaje de "no hay resultados" se siente rota.

---

## Estilos

Con **Tailwind CSS 4**: clases directamente en el JSX, sin archivos `.css` por
pantalla.

- **La paleta vive en `estilos/globales.css`**, dentro de `@theme`, y es la única
  que existe: `--color-*: initial` borra la de Tailwind. `bg-azul-950` funciona;
  `bg-blue-500` ni siquiera se genera. Si falta un tono, se agrega ahí con nombre.
- Nada de colores escritos a mano dentro de los componentes, ni en `className`
  (`bg-[#112853]`) ni en `style`.
- Lo mismo con los tamaños de texto y las animaciones que no están en la escala
  de Tailwind: se declaran en `@theme` (`text-titulo`, `animate-brillo`).
- La fuente es **Inter**, instalada con npm (`@fontsource-variable/inter`): no se
  descarga nada a mano y funciona sin internet.
- Pensado primero para el celular, que es desde donde entra casi todo el mundo;
  lo de escritorio se agrega con `lg:`.

### Íconos

Con **Phosphor** (`@phosphor-icons/react`), instalado con npm: no se descarga
ningún paquete a mano. Cada ícono se importa por su nombre con el sufijo `Icon`
(`import { BellIcon } from '@phosphor-icons/react'`), toma el color del texto
(`currentColor`) y el tamaño con `size`.

- Si el ícono acompaña a un texto, es decoración: `aria-hidden`.
- Si es la única pista de lo que hace un botón, el botón lleva `aria-label`.
- Las secciones del menú y sus íconos están en `configuracion/menu.js`.

---

## Imports

Orden: librerías externas → imports con `@/` → imports relativos. Los separa una
línea en blanco. `eslint` avisa de los imports sin usar.

---

## Variables de entorno

- Solo las que empiezan por `VITE_` llegan al navegador.
- **Nada de secretos**: el bundle es público y cualquiera lo puede leer.
- Toda variable nueva se agrega también a `.env.example` y al `compose.yaml`.

---

## Pruebas

Con Vitest + Testing Library. Se prueba lo que ve el usuario, no la
implementación:

```bash
./dev.sh test front
docker compose exec frontend npm run test
```

Prioridad: utilidades puras, DTOs, hooks con lógica y componentes de formulario.

Una pantalla se prueba sin backend: se simula su capa `api/` con `vi.mock`, se
monta con `renderizarEnRuta` de `src/pruebas/` y los errores de la API se
fabrican con `errorDeApi`. Ver las pruebas de `modulos/autenticacion/paginas/`.

---

## Dependencias

Se instalan dentro del contenedor, y `package.json` y `package-lock.json` se
suben juntos:

```bash
docker compose exec frontend npm install <paquete>
```

Al resto del equipo le llegan con un `./dev.sh up`, sin `--build`: el contenedor
compara el `package-lock.json` con el de la última instalación y, si cambió,
instala antes de arrancar Vite (`scripts/entrypoint.sh`).

---

## Antes de subir

```bash
./dev.sh lint      # eslint
./dev.sh format    # prettier
./dev.sh test front
```

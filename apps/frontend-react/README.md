# Frontend — React

Interfaz web del sistema de inventario **El Tapaso**.

| | |
| --- | --- |
| Runtime | Node.js 24 LTS |
| Librería | React 19 (JavaScript, sin TypeScript) |
| Build tool | Vite 8 |
| Datos | Axios + TanStack Query |
| Rutas | React Router 7 |
| Estilos | Tailwind CSS 4, con la paleta en `src/estilos/globales.css` |
| Fuente | Inter (`@fontsource-variable/inter`, sin descargas a mano) |
| Íconos | Phosphor (`@phosphor-icons/react`) |

## Arranque rápido

Desde la **raíz del repositorio**:

```bash
./dev.sh up frontend
```

Queda en `http://localhost:5173`, en la pantalla de iniciar sesión. Si alguien
agregó una dependencia, el contenedor la instala solo al arrancar. Guía
completa: [`docs/guias/guia-instalacion.md`](../../docs/guias/guia-instalacion.md).

## Estructura

Explicada carpeta por carpeta en
[`docs/frontend/estructura.md`](../../docs/frontend/estructura.md).

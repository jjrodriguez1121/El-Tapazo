# App: `clientes`

Quién compra en el bar o en un evento: la ficha de la persona, con su documento
y su fecha de nacimiento.

**Modelos:** `Cliente`.

Un cliente **no** es un usuario: no inicia sesión ni tiene contraseña. `usuarios`
es para quien opera el sistema (admin, mesero, cajero); esta tabla es para quien
consume. Las tiendas que compran al por mayor son otra cosa y viven en
[`distribucion`](../distribucion/README.md): se identifican por NIT y pagan a
crédito, no por documento y esa misma noche.

La pulsera NFC no guarda nada de esto: solo aporta su UID de fábrica, que lleva
hasta la fila de `clientes_evento` activa y de ahí a esta ficha.

## Qué se puede hacer

`/api/v1/clientes/` — CRUD, más `POST {id}/desactivacion/`,
`GET por-documento/` y `GET {id}/historial/`.

**Los permisos no son los mismos para todo.** El mesero y el cajero registran y
buscan clientes, porque es lo que hacen en la barra toda la noche; desactivar
una ficha es de administrador.

**Ser menor de edad avisa, no bloquea** (decisión 7 del plan de negocio). La
ficha se crea igual y la respuesta trae `es_menor_de_edad` para que la pantalla
lo pinte en rojo: quien decide si se le vende es la persona de la barra.

`GET {id}/historial/` lee tablas de `eventos`, y esa dirección es la segura:
`eventos` apunta a `clientes` por nombre, nunca con un `import`.

## Carpetas

| Carpeta | Qué va aquí |
| --- | --- |
| `api/` | Vistas, serializers y routers (capa HTTP). |
| `dtos/` | Objetos de transferencia de datos entre capas (dataclasses). |
| `excepciones/` | Excepciones propias del dominio de esta app. |
| `migrations/` | Migraciones de base de datos (nombre exigido por Django). |
| `permisos/` | Permisos de DRF específicos de esta app. |
| `repositorios/` | Acceso a datos: consultas al ORM aisladas del resto. |
| `selectores/` | Lecturas / consultas de negocio. |
| `servicios/` | Reglas de negocio y escrituras. |
| `pruebas/` | Pruebas de esta app. |
| `validadores/` | Validaciones reutilizables del dominio. |

Reglas de código: [`varios/reglas/`](../../../varios/reglas/README.md) ·
Arquitectura: [`docs/backend/estructura.md`](../../../docs/backend/estructura.md)

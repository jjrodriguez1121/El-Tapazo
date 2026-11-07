# El Tapaso

**El sistema que hace que la plata del bar no se vaya por los huecos que nadie
mira.** Inventario, barra, mayoreo y caja en un solo sitio, con pulseras NFC en
la muñeca del cliente y aparatos vigilando la puerta — para que
el negocio necesite menos gente contando y tenga números que de verdad cuadran.

---

## 1. El problema, sin adornos

En un bar la plata no se pierde en un robo grande. Se pierde en goteo, y casi
siempre en los mismos cinco sitios:

| El hueco | Qué pasa hoy en un negocio sin sistema |
| --- | --- |
| **La botella que sale y no se factura** | Entra fría a la nevera, sale en la mano de alguien y nunca aparece en una comanda. Al final de la noche falta producto y no hay a quién preguntarle |
| **El que se va sin pagar** | La cuenta queda abierta, el cliente salió por la puerta, y nadie se dio cuenta hasta el cierre |
| **El conteo a mano** | Alguien con una libreta contando cajas. Lento, aburrido, y un número que nadie puede auditar después |
| **La caja que no cuadra** | Se vendió «como unos» tantos, se cobró «más o menos» tanto, y la diferencia se archiva como misterio |
| **El mayorista que debe** | La tienda quedó a 30 días. ¿Cuál tienda? ¿Cuántos días lleva? ¿Abonó algo? Está en la cabeza del dueño o en un cuaderno |

Los cinco tienen el mismo origen: **hay tramos de la operación donde el sistema
no ve nada porque depende de que una persona se acuerde de teclearlo.**

Este proyecto ataca exactamente eso.

---

## 2. La idea, en una frase

> Que cada movimiento de mercancía y cada peso cobrado deje rastro **solo**,
> por el propio acto de trabajar — no porque alguien se acuerde de registrarlo.

De ahí salen las dos ganancias que sostienen todo el proyecto: **menos mano de
obra** y **contabilidad que cuadra**.

---

## 3. Menos mano de obra — dónde exactamente

No es «el software ahorra empleados» en abstracto. Es tarea por tarea:

| Tarea | Como se hace sin sistema | Como se hace aquí | Lo que se ahorra |
| --- | --- | --- | --- |
| **Abrir la jornada** | Alguien crea el turno/la planilla del día | Se abre sola al primer uso, por ubicación, sin que nadie la cree | El ritual de apertura, y el error de partir una noche en dos jornadas |
| **Llevar la cuenta de cada cliente** | Un cajero con la comanda de papel por mesa | La **pulsera NFC** en la muñeca: la cuenta viaja con la persona, no con el papel | Un cajero atado a la lista de cuentas |
| **Descontar del inventario** | Conteo al final de la noche, a ojo | La comanda **descuenta al crearse**. El stock siempre está al día | La jornada de conteo, y las diferencias que salían de ahí |
| **Vigilar quién se va debiendo** | Un portero preguntando de memoria | El **punto de control NFC** de la salida: pasa la pulsera, verde o rojo | Un portero convertido en cobrador |
| **Cerrar caja** | Sumar papeles y esperar que cuadre | El informe de cierre lo calcula la base de datos, y **cerrar con cuentas abiertas se bloquea** listando cuáles | La hora de cuadre, y el «mañana lo revisamos» |
| **Saber quién debe en mayoreo** | Un cuaderno | Cada pedido con su plazo, sus abonos y su mora calculada | El seguimiento manual de cartera |
| **Contar cajas en bodega** *(propuesta)* | Botella por botella | Tag NFC en el cartón: pasar la caja dispara el movimiento | El conteo unitario |
| **Teclear la factura del proveedor** *(propuesta)* | Línea por línea a mano | Foto o PDF → borrador armado → alguien solo revisa | La transcripción, no la revisión |

La lectura correcta no es «sobra gente»: es que **la misma gente deja de hacer
trabajo de registro y vuelve a atender clientes**, que es lo que produce plata.
Un mesero que no hace fila en la caja atiende más mesas.

---

## 4. Mejor contabilidad — por qué estos números sí se pueden defender

La diferencia entre «un sistema que anota ventas» y uno contable de verdad está
en unas pocas decisiones, y aquí están todas tomadas a propósito:

- **El kardex es la única fuente de verdad.** Cada entrada, salida, traslado y
  ajuste es un movimiento con fecha, motivo y responsable. La existencia no es
  un número que alguien edita: es la suma de su historia.
- **Nada se borra.** Una anulación es un movimiento contrario, no un `DELETE`.
  El rastro queda completo, y cancelar dos veces no repone de más porque se
  devuelve **el neto del kardex**, no las líneas del pedido.
- **El precio se congela en la línea de venta.** Cambiar la lista de precios hoy
  no reescribe las facturas del mes pasado. Y el precio **no viaja en la
  petición**: lo pone el servidor, para que nadie fije el precio de su propia
  cerveza.
- **Sin existencias, se bloquea. Siempre.** Sin excepción ni para el
  administrador. No se vende lo que no hay, así que el inventario nunca queda
  en negativo «para arreglarlo después».
- **Toda venta es una transacción.** Pedido, líneas, kardex y saldos entran
  juntos o no entra nada. Y aguanta dos meseros vendiendo el mismo producto en
  el mismo instante — está probado con pruebas de concurrencia, no supuesto.
- **Cada peso cobrado tiene un solo destino.** La base de datos obliga a que un
  pago sea de un grupo, de una persona, o de una venta de mostrador; nunca de
  dos cosas a la vez.
- **Un negocio no ve al otro.** El `negocio_id` sale siempre del usuario
  autenticado, jamás de la petición, y pedir algo ajeno responde **404, no
  403** — ni siquiera se filtra que existe.
- **Cada canal reporta lo suyo.** El resumen dice cuánto puso la barra y cuánto
  puso el mayoreo, en el mismo periodo y con el mismo catálogo.

---

## 5. Las pulseras: el corazón de la operación

El cliente entra, se le presta una pulsera NFC y esa pulsera **es** su cuenta.

- La cuenta puede ser personal o de **grupo** (la mesa completa paga junta).
- El sistema avisa si el cliente es **menor de edad** — avisa, no bloquea: la
  decisión es del negocio, pero queda en pantalla y en rojo.
- Hay **alertas de consumo**: un umbral por cuenta que, al cruzarse, deja
  registro de quién lo atendió y qué hizo. Es una herramienta de
  responsabilidad, no un adorno.
- La pulsera solo guarda el UID del chip. A quién se le prestó es un dato
  aparte, nuevo cada noche: la misma pulsera sirve mil veces sin arrastrar
  historia de nadie.
- Cobrar **bloquea la cuenta** y vuelve a comprobarla después del bloqueo, para
  que dos cajeros cobrando la misma pulsera no generen dos pagos.

---

## 6. La puerta: el punto de control NFC

El aparato de la salida. La persona pasa la pulsera y el aparato responde:

- **cuenta saldada** → LED verde y pitido corto.
- **cuenta abierta con saldo** → LED rojo y el zumbador sonando.

Cuesta **10 a 15 USD en piezas** (ESP32 + lector RC522 + dos LEDs + zumbador) y
sustituye a alguien parado en la puerta confiando en su memoria.

Dos cosas que este proyecto dice de frente en vez de venderlas de más:

- **NFC no detecta a distancia.** El alcance son 2–5 cm. Esto es un torniquete,
  no un arco de tienda: la persona pasa la pulsera. El arco que pita solo
  necesita UHF RFID y lectores de cientos de dólares.
- **El aparato tiene su propio token**, no la sesión de un cajero. Si alguien
  desarma la caja y saca el token, se revoca ese y ya. Además el endpoint va con
  freno de peticiones y devuelve **solo el nombre y el monto** — ni documento ni
  teléfono —, porque cualquiera con un lector de tres dólares podría ponerse a
  preguntar cuánto debe cada persona del bar.

Todo el montaje, pin por pin y con los videos de cada paso, está en
[`varios/hardware/`](varios/hardware/README.md).

---

## 7. La nevera: el último hueco, y cómo pensamos cerrarlo

> **Estado: propuesta.** Vive en [`varios/por-aceptar/`](varios/por-aceptar/README.md)
> — es una idea con su diseño listo, **no algo construido**. Se documenta aquí
> porque es la pieza que completa el planteamiento del sistema.

Hoy el sistema ve dos puntos: **la caja que entra fría** a la nevera y **la
comanda que sale** cuando un mesero vende. Entre esos dos puntos hay un tramo
ciego: la botella que sale de la nevera y nunca llega a una comanda —
autoconsumo, un regalo, algo que se lleva alguien — el sistema no la ve nunca,
porque nadie la tecleó.

La propuesta cierra ese tramo con tres piezas baratas en la puerta de la
nevera: **una báscula** debajo (celda de carga + HX711, ~5 USD), **un lector
NFC** y **tres botones**.

### La clave: se declara *antes* de abrir, no después

1. El mesero acerca **su credencial personal** (no la pulsera de un cliente).
2. Antes de abrir, declara qué va a hacer: **sacar**, **organizar** o
   **reponer**.
3. Se abre una ventana corta (≈30 s) en la que todo cambio de peso se atribuye
   a esa persona y a esa intención.
4. Al cerrarse, el sistema compara **lo declarado contra lo medido**.

El orden es el truco entero. Si se declarara después, la persona solo estaría
describiendo lo que la báscula ya iba a medir, y el cruce no detectaría nada.
Declarando antes, **una contradicción es información real**:

| Declaró | Midió la báscula | Qué hace el sistema |
| --- | --- | --- |
| Sacar | Bajó peso, cuadra con unidades enteras | Descuenta solo. Nadie teclea nada |
| Reponer | Subió peso, cuadra | Registra la entrada sola |
| Organizar | Bajó peso | **Alerta**, con nombre y hora exacta |
| Reponer | Bajó peso | **Alerta, la más seria de todas** |
| Cualquiera | Sin cambio, o sin declarar | Aviso suave, o lectura guardada «sin declarar» |

Y al cerrar la jornada, el cruce que lo vuelve accionable: **lo que cada mesero
sacó** (báscula) contra **lo que ese mismo mesero facturó** (las comandas, que
ya guardan quién las tomó).

### Lo que esto no hace — y se dice claro

No distingue «sacó 2 y no repuso» de «sacó 2 y repuso 2» — el peso neto es el
mismo. Tampoco impide que alguien mienta al declarar. **Lo que sí logra es que
un error o una mentira deje una contradicción concreta y con nombre**, en vez
de un faltante anónimo al final de la noche. Eso ya es un cambio de categoría.

La versión con **chapa eléctrica** (la nevera no abre sin credencial válida) es
posible por 5–10 USD más, y está deliberadamente aplazada: una nevera trabada un
viernes en hora pico por un aparato que falló es un problema real. Primero
observar, después impedir — si hace falta.

---

## 8. Dos canales, un solo catálogo

Un mismo negocio vende por dos puertas muy distintas, y el sistema no las
confunde:

| | **Barra / evento** | **Distribución (mayoreo)** |
| --- | --- | --- |
| A quién | Al cliente de la noche | A tiendas, B2B |
| Precio | `precio_evento` | `precio_mayorista` |
| Cuándo sale el stock | Al **crear la comanda** | Al **despachar** (ya va en el camión) |
| Cómo se paga | De un solo pago que salda la cuenta | **Con abonos**, a crédito y con días de plazo |
| Si algo sale mal | Cancelar devuelve el stock | `no_entregado` **con motivo obligatorio**, la mercancía vuelve a la bodega en el acto y el pedido se puede volver a despachar |

Ciclo de un pedido mayorista:

```
pendiente ──despachar──► en_ruta ──entregar──► entregado
    ▲                       │
    │                  no entregar
    │                       ▼
    └───── despachar ── no_entregado ──► cancelado
```

Y por encima de los dos, el informe que suma: **cuánto puso cada canal**.

---

## 9. Quién puede hacer qué

Tres roles, con la frontera puesta donde está el dinero:

| | Admin | Cajero | Mesero |
| --- | --- | --- | --- |
| Abrir y cerrar la caja | sí | sí | **no** |
| Abrir grupos y cuentas, asignar pulseras | sí | sí | sí |
| Tomar y entregar comandas | sí | sí | sí |
| Cobrar, liberar cuentas, cancelar comandas | sí | sí | **no** |
| Catálogo, inventario, mayoreo, lectores | sí | **no** | **no** |

**No hay registro público.** Las cuentas nacen de una invitación, y cada negocio
lo da de alta el staff de la plataforma. Un bar no se crea solo desde una
pantalla de «regístrate gratis».

---

## 10. Estado del proyecto

| Parte | Estado |
| --- | --- |
| Modelo de datos — 24 tablas con sus restricciones | **[✔] Completo** |
| Núcleo compartido — permisos, aislamiento por negocio, errores | **[✔] Completo** |
| `catalogo`, `clientes` | **[✔] Completo** |
| `inventario` — kardex, traslados, ajustes, anulaciones, valorización | **[✔] Completo** |
| `eventos` — jornada, cuentas, venta, cobro, alertas, punto de control | **[✔] Completo** |
| `distribucion` — pedido, despacho, no entrega, abonos y mora | **[✔] Completo** |
| `negocios` — alta, suspensión y resumen por canal | **[✔] Completo** |
| **Backend entero** | **[✔] Completo · 348 pruebas en verde** |
| Frontend — pantallas de identidad y panel principal | **En curso**, con su suite de pruebas en verde |
| Frontend — pantallas de la operación | Lo siguiente |
| Hardware — punto de control NFC | Diseñado y documentado, por armar |
| Nevera con báscula · tags en cajas · lector de facturas | Propuestas, sin aprobar |

Las decisiones de negocio que mandan sobre cualquier intuición están en
[`varios/planes/plan-logica-de-negocio.md`](varios/planes/plan-logica-de-negocio.md);
lo que todavía no es plan, en [`varios/por-aceptar/`](varios/por-aceptar/README.md).

---

## 11. Cómo está construido

| Parte | Tecnología | Versión |
| --- | --- | --- |
| Backend | Python / Django / Django REST Framework | 3.13 / 5.2 LTS / 3.16 |
| Base de datos | PostgreSQL | 18 |
| Frontend | Node.js / React / Vite | 24 LTS / 19 / 8 |
| Hardware | ESP32 + RC522 (NFC 13.56 MHz) | — |
| Entorno | Docker + Docker Compose | — |

La arquitectura no es negociable y por eso el código se lee igual en las siete
apps: **la lógica vive en `servicios/` (escrituras) y `selectores/`
(lecturas)**, `Modelo.objects` solo aparece dentro de `repositorios/`, y las
flechas no se invierten — `api → servicios → repositorios → models`. Ni una
regla de negocio en vistas, serializers, `save()` ni señales. Y la base de datos
es la última línea de defensa: cada regla que se puede declarar como
restricción, se declara.

---

## 12. Arranque rápido

```bash
git clone <url-del-repo>
cd El-Tapaso
./dev.sh up --build
```

El script `dev.sh` crea el `.env`, **busca puertos libres** (si el 8000 o el 5432
ya los usa otro programa, toma el siguiente disponible), levanta los tres
contenedores y al final te imprime las URLs:

| Servicio | URL (puertos por defecto) |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| Documentación de la API | http://localhost:8000/api/docs/ |
| Admin de Django | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5432 |

```bash
./dev.sh down       # apagar
./dev.sh status     # ver estado y URLs
./dev.sh logs       # ver logs
./dev.sh help       # todas las opciones
```

Paso a paso completo en [`docs/guias/guia-instalacion.md`](docs/guias/guia-instalacion.md).

---

## 13. Estructura del repositorio

```
El-Tapaso/
├── apps/
│   ├── backend-django/     API en Django (ver docs/backend/estructura.md)
│   └── frontend-react/     Interfaz en React (ver docs/frontend/estructura.md)
├── docker/                 Configuración auxiliar de contenedores (nginx, init de la BD)
├── docs/                   Cómo instalar, levantar y trabajar en el proyecto
├── varios/
│   ├── planes/             Lo decidido: la lógica de negocio, fase por fase
│   ├── bd/                 El diseño de las 24 tablas y su porqué
│   ├── hardware/           El punto de control NFC: qué comprar y cómo se arma
│   ├── por-aceptar/        Ideas con diseño listo, esperando decisión
│   └── reglas/             Las reglas que sigue el código
├── dev.sh                  Script para encender/apagar el entorno
├── compose.yaml            Entorno de desarrollo
└── .env.example            Plantilla de variables de entorno
```

---

## 14. Documentación

**Para empezar a trabajar**

- [Guía de instalación](docs/guias/guia-instalacion.md) — de cero a la app corriendo.
- [Guía de comandos](docs/guias/guia-comandos.md) — chuleta del día a día.
- [Guía de base de datos](docs/guias/guia-base-de-datos.md) — modo local vs Supabase.
- [Guía de Docker](docs/guias/guia-docker.md) — cómo funciona el entorno y cómo arreglar problemas.
- [Flujo de trabajo con Git](docs/guias/guia-flujo-git.md) — ramas, commits y PRs.

**Para escribir código aquí**

- [Estructura del backend](docs/backend/estructura.md) · [Convenciones](docs/backend/convenciones.md) · [Crear una app nueva](docs/backend/crear-nueva-app.md)
- [Estructura del frontend](docs/frontend/estructura.md) · [Convenciones](docs/frontend/convenciones.md)

import {
  ChatCircleDotsIcon,
  GearSixIcon,
  HandCoinsIcon,
  PackageIcon,
  ReceiptIcon,
  ShoppingCartIcon,
  SquaresFourIcon,
  TagIcon,
  TruckIcon,
  UsersIcon,
  WalletIcon,
} from '@phosphor-icons/react'

import { RUTAS } from './rutas'

/*
 * Las secciones del menú lateral, en el orden en que se ven.
 *
 * `soloAdministrador` sigue la decisión 6 del plan de negocio: catálogo,
 * inventario y cartera son módulos administrativos.
 * Esconder el enlace es comodidad para quien usa la pantalla; quien lo impide
 * de verdad es el backend, que responde 403.
 */
export const SECCIONES_DEL_MENU = [
  {
    titulo: 'Principal',
    elementos: [
      { ruta: RUTAS.inicio, etiqueta: 'Dashboard', Icono: SquaresFourIcon },
      { ruta: RUTAS.puntoDeVenta, etiqueta: 'Punto de venta', Icono: ShoppingCartIcon },
      { ruta: RUTAS.ventas, etiqueta: 'Ventas', Icono: ReceiptIcon },
    ],
  },
  {
    titulo: 'Inventario',
    elementos: [
      { ruta: RUTAS.productos, etiqueta: 'Productos', Icono: PackageIcon, soloAdministrador: true },
      { ruta: RUTAS.compras, etiqueta: 'Compras', Icono: ShoppingCartIcon, soloAdministrador: true },
      { ruta: RUTAS.categorias, etiqueta: 'Categorías', Icono: TagIcon, soloAdministrador: true },
      {
        ruta: RUTAS.proveedores,
        etiqueta: 'Proveedores',
        Icono: TruckIcon,
        soloAdministrador: true,
      },
    ],
  },
  {
    titulo: 'Cartera',
    elementos: [
      {
        ruta: RUTAS.cuentasPorPagar,
        etiqueta: 'Cuentas por pagar',
        Icono: WalletIcon,
        soloAdministrador: true,
      },
      {
        ruta: RUTAS.cartera,
        etiqueta: 'Cuentas por cobrar',
        Icono: HandCoinsIcon,
        soloAdministrador: true,
      },
    ],
  },
  {
    titulo: 'Clientes',
    elementos: [
      { ruta: RUTAS.clientes, etiqueta: 'Clientes', Icono: UsersIcon },
      { ruta: RUTAS.pqrs, etiqueta: 'PQRs', Icono: ChatCircleDotsIcon },
    ],
  },
]

/** Va aparte, abajo del todo, junto a «Salir». */
export const CONFIGURACION_DEL_MENU = {
  ruta: RUTAS.configuracion,
  etiqueta: 'Configuración',
  Icono: GearSixIcon,
  soloAdministrador: true,
}

/** Todos los destinos del menú, para registrar sus rutas. */
export const ELEMENTOS_DEL_MENU = [
  ...SECCIONES_DEL_MENU.flatMap((seccion) => seccion.elementos),
  CONFIGURACION_DEL_MENU,
]

export const puedeVerElemento = (elemento, esAdministrador) =>
  esAdministrador || !elemento.soloAdministrador

/** Las secciones con lo que le toca ver a quien entró. Una sección que queda vacía no se enseña. */
export function seccionesVisibles(esAdministrador) {
  return SECCIONES_DEL_MENU.map((seccion) => ({
    ...seccion,
    elementos: seccion.elementos.filter((elemento) => puedeVerElemento(elemento, esAdministrador)),
  })).filter((seccion) => seccion.elementos.length > 0)
}

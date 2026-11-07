/*
 * Las clases de una fila del menú lateral, compartidas por los enlaces y por el
 * botón de «Salir»: se ven igual, pero uno lleva a otra pantalla y el otro hace
 * algo, y cada uno tiene que ser lo que es.
 */

export const CLASES_DE_FILA_DEL_MENU =
  'flex w-full items-center gap-3 rounded-[11px] px-2.75 py-2.5 text-left text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-azul-300'

export const CLASES_DE_FILA_INACTIVA = 'text-azul-300 hover:bg-blanco/6 hover:text-blanco'

export const CLASES_DE_FILA_ACTIVA = 'bg-azul-600/40 text-blanco'

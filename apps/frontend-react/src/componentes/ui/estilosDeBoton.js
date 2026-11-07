/*
 * Las clases de los botones, compartidas entre el <button> y el <Link> que se
 * ven iguales. Para quien usa la pantalla, «ir a iniciar sesión» y «volver a
 * intentar» son el mismo botón; para el lector de pantalla, uno es un enlace y
 * el otro una acción, y cada uno tiene que ser lo que es.
 */

export const CLASES_BOTON_PRINCIPAL =
  'flex h-13 w-full items-center justify-center gap-2.5 rounded-xl bg-azul-950 px-4 text-base font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-300 disabled:cursor-progress disabled:bg-azul-600'

export const CLASES_BOTON_DE_TEXTO =
  'self-center rounded text-sm font-bold text-azul-600 underline underline-offset-3 hover:text-azul-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-300'

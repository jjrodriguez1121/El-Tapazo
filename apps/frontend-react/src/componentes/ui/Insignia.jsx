import { CLASES_POR_TONO } from './tonos'

/** Una etiqueta pequeña y redonda para un estado o una cifra al margen. */
export default function Insignia({ children, tono = 'neutro' }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.75 text-xs font-semibold whitespace-nowrap ${CLASES_POR_TONO[tono]}`}
    >
      {children}
    </span>
  )
}

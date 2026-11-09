/*
 * Cómo se escriben los números y las fechas en pantalla, en español de Colombia.
 */

// `useGrouping: 'always'` porque en español un número de cuatro cifras no lleva
// punto por defecto: saldría «$9500» al lado de «$12.000».
const NUMEROS = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0, useGrouping: 'always' })
const ZONA_HORARIA = 'America/Bogota'

const FECHA_LARGA = new Intl.DateTimeFormat('es-CO', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

const FECHA_CORTA = new Intl.DateTimeFormat('es-CO', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  timeZone: ZONA_HORARIA,
})

const FECHA_HORA = new Intl.DateTimeFormat('es-CO', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: ZONA_HORARIA,
})

/** «$1.240.000». Pesos sin decimales, que es como se cobra. */
export const formatearPesos = (valor) => `$${NUMEROS.format(valor)}`

/** «1.240». Cantidades con separador de miles. */
export const formatearCantidad = (valor) => NUMEROS.format(valor)

/** «Jueves, 11 de septiembre de 2026». */
export function formatearFechaLarga(fecha) {
  const texto = FECHA_LARGA.format(fecha)
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/** «11/09/2026». */
export function formatearFechaCorta(fecha) {
  const d =
    typeof fecha === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(fecha)
      ? new Date(`${fecha}T12:00:00Z`)
      : typeof fecha === 'string'
        ? new Date(fecha)
        : fecha
  return FECHA_CORTA.format(d)
}

/** Fecha y hora del servidor expresada siempre en la hora de Colombia. */
export function formatearFechaHora(fecha) {
  return FECHA_HORA.format(typeof fecha === 'string' ? new Date(fecha) : fecha)
}

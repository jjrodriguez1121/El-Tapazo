const ZONA_HORARIA = 'America/Bogota'
const PARTES_FECHA = new Intl.DateTimeFormat('en-CA', {
  timeZone: ZONA_HORARIA,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

export function obtenerFechaLocalIso(valor) {
  if (valor == null || valor === '') return ''
  if (typeof valor === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor

  const fecha = valor instanceof Date ? valor : new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''

  const partes = Object.fromEntries(
    PARTES_FECHA.formatToParts(fecha).map(({ type, value }) => [type, value])
  )
  return `${partes.year}-${partes.month}-${partes.day}`
}

export function obtenerFechaMinimaVencimiento() {
  const manana = new Date(`${obtenerFechaLocalIso(new Date())}T12:00:00Z`)
  manana.setUTCDate(manana.getUTCDate() + 1)
  return manana.toISOString().slice(0, 10)
}

export function estaEnRangoDeFechas(fecha, desde, hasta) {
  const fechaIso = obtenerFechaLocalIso(fecha)
  return Boolean(fechaIso && (!desde || fechaIso >= desde) && (!hasta || fechaIso <= hasta))
}

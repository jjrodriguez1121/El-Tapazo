export function obtenerFechaLocalIso(valor) {
  if (typeof valor === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor

  const fecha = valor instanceof Date ? valor : new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''

  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

export function estaEnRangoDeFechas(fecha, desde, hasta) {
  const fechaIso = obtenerFechaLocalIso(fecha)
  return Boolean(fechaIso && (!desde || fechaIso >= desde) && (!hasta || fechaIso <= hasta))
}

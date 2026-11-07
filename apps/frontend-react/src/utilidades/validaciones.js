const PATRON_DE_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PATRON_DE_SKU = /^[A-Z]{3}-\d{3,6}$/

export const LARGO_MAXIMO_DE_CORREO = 150

export function validarCorreo(correo) {
  const limpio = correo.trim()
  if (!limpio) return 'Escribe tu correo.'
  if (!PATRON_DE_CORREO.test(limpio)) return 'Ese correo no parece válido.'
  return ''
}

export function validarCorreoOpcional(correo) {
  return correo.trim() ? validarCorreo(correo) : ''
}

export const validarObligatorio = (valor, mensaje) =>
  (String(valor).trim() ? '' : mensaje)

export function validarTelefono(telefono) {
  const limpio = telefono.trim()
  if (!/^[+\d().\-\s]+$/.test(limpio)) {
    return 'El teléfono solo puede contener números y símbolos de formato.'
  }
  const digitos = telefono.replace(/\D/g, '')
  if (!digitos) return 'Escribe un teléfono de contacto.'
  if (digitos.length < 7 || digitos.length > 15) {
    return 'El teléfono debe tener entre 7 y 15 dígitos.'
  }
  return ''
}

export function validarSku(sku) {
  const normalizado = sku.trim().toUpperCase()
  if (!normalizado) return 'Escribe el código SKU.'
  if (!PATRON_DE_SKU.test(normalizado)) {
    return 'Usa el formato ABC-123 (tres letras y entre tres y seis números).'
  }
  return ''
}

export function validarDocumento(documento, etiqueta = 'El documento') {
  const limpio = documento.trim()
  const alfanumericos = limpio.replace(/[^a-z\d]/gi, '')
  if (!limpio) return `Escribe ${etiqueta.toLowerCase()}.`
  if (!/^[a-z\d.\-\s]+$/i.test(limpio) || alfanumericos.length < 5 || limpio.length > 30) {
    return `${etiqueta} debe tener entre 5 y 30 caracteres válidos.`
  }
  return ''
}

export function validarNumeroNoNegativo(valor, etiqueta, { entero = false } = {}) {
  const texto = String(valor).trim()
  if (!texto) return `Ingresa ${etiqueta.toLowerCase()}.`

  const numero = Number(texto)
  if (!Number.isFinite(numero) || numero < 0) return `${etiqueta} debe ser un número igual o mayor que cero.`
  if (entero && !Number.isInteger(numero)) return `${etiqueta} debe ser un número entero.`
  return ''
}

export function validarFechaNacimiento(fecha) {
  if (!fecha) return 'Indica la fecha de nacimiento.'
  if (fecha < '1900-01-01') return 'La fecha de nacimiento debe ser posterior al año 1900.'
  if (fecha > new Date().toISOString().slice(0, 10)) {
    return 'La fecha de nacimiento no puede ser futura.'
  }
  return ''
}
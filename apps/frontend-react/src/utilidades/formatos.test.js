import { expect, test } from 'vitest'

import {
  formatearCantidad,
  formatearFechaCorta,
  formatearFechaHora,
  formatearFechaLarga,
  formatearPesos,
} from './formatos'

test('formatearPesos escribe pesos sin decimales y con punto de miles', () => {
  expect(formatearPesos(1240000)).toBe('$1.240.000')
  expect(formatearPesos(9500)).toBe('$9.500')
  expect(formatearPesos(0)).toBe('$0')
})

test('formatearCantidad pone el punto de miles también en cuatro cifras', () => {
  expect(formatearCantidad(1240)).toBe('1.240')
})

test('formatearFechaLarga escribe el día completo con mayúscula inicial', () => {
  expect(formatearFechaLarga(new Date(2026, 8, 11))).toBe('Viernes, 11 de septiembre de 2026')
})

test('formatearFechaCorta formatea fecha en día/mes/año', () => {
  expect(formatearFechaCorta(new Date('2026-09-11T12:00:00-05:00'))).toBe('11/09/2026')
})

test('formatearFechaCorta conserva la fecha civil y convierte timestamps a horario de Bogotá', () => {
  expect(formatearFechaCorta('2026-11-08')).toBe('08/11/2026')
  expect(formatearFechaCorta('2026-11-09T04:30:00Z')).toBe('08/11/2026')
})

test('formatearFechaHora muestra el timestamp en horario de Bogotá', () => {
  expect(formatearFechaHora('2026-11-09T04:30:00Z')).toContain('8')
  expect(formatearFechaHora('2026-11-09T04:30:00Z')).toMatch(/11:30 p\.\s*m\./)
})

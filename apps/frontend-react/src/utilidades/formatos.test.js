import { expect, test } from 'vitest'

import {
  formatearCantidad,
  formatearFechaCorta,
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
  expect(formatearFechaCorta(new Date(2026, 8, 11))).toBe('11/09/2026')
})

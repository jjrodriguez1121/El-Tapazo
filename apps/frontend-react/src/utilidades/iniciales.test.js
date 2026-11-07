import { expect, test } from 'vitest'

import { iniciales } from './iniciales'

test('toma la inicial de las dos primeras palabras, en mayúscula', () => {
  expect(iniciales('ana ríos')).toBe('AR')
  expect(iniciales('Bar La Esquina')).toBe('BL')
})

test('con una sola palabra devuelve una sola inicial, y aguanta espacios de más', () => {
  expect(iniciales('  Kevin  ')).toBe('K')
})

test('con un nombre vacío no inventa nada', () => {
  expect(iniciales('')).toBe('')
})

import { expect, test } from 'vitest'

import {
  validarCorreo,
  validarCorreoOpcional,
  validarDocumento,
  validarFechaNacimiento,
  validarNumeroNoNegativo,
  validarObligatorio,
  validarSku,
  validarTelefono,
} from './validaciones'

test('valida correo requerido y opcional', () => {
  expect(validarCorreo('ana@bar')).not.toBe('')
  expect(validarCorreo(' ana@bar.com ')).toBe('')
  expect(validarCorreoOpcional('  ')).toBe('')
})

test('valida campos requeridos y teléfonos con formato común', () => {
  expect(validarObligatorio('  ', 'Campo obligatorio.')).toBe('Campo obligatorio.')
  expect(validarTelefono('+57 300 123 4567')).toBe('')
  expect(validarTelefono('123')).not.toBe('')
  expect(validarTelefono('teléfono 1234567')).not.toBe('')
})

test('valida SKU ignorando espacios y mayúsculas', () => {
  expect(validarSku(' cer-001 ')).toBe('')
  expect(validarSku('CODIGO1')).not.toBe('')
})

test('valida documento, fechas y números', () => {
  expect(validarDocumento('900.123.456-7', 'El NIT')).toBe('')
  expect(validarDocumento('12', 'El documento')).not.toBe('')
  expect(validarFechaNacimiento('2099-01-01')).not.toBe('')
  expect(validarNumeroNoNegativo('-1', 'El precio')).not.toBe('')
  expect(validarNumeroNoNegativo('2.5', 'El stock', { entero: true })).not.toBe('')
})
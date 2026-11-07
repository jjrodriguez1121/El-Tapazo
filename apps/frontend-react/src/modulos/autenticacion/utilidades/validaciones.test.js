import { expect, test } from 'vitest'

import { validarCorreo, validarObligatorio } from './validaciones'

test('un correo vacío pide que lo escriban', () => {
  expect(validarCorreo('   ')).toBe('Escribe tu correo.')
})

test('un correo sin dominio no es válido', () => {
  expect(validarCorreo('ana@bar')).toBe('Ese correo no parece válido.')
})

test('un correo bien escrito pasa aunque traiga espacios alrededor', () => {
  expect(validarCorreo(' ana@bar.com ')).toBe('')
})

test('validarObligatorio devuelve el mensaje solo si el campo está vacío', () => {
  expect(validarObligatorio('  ', 'Escribe tu nombre.')).toBe('Escribe tu nombre.')
  expect(validarObligatorio('Luis', 'Escribe tu nombre.')).toBe('')
})

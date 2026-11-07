import { expect, test } from 'vitest'

import { contrasenaEsValida, evaluarContrasena } from './reglasDeContrasena'

test('seis caracteres con letras y números es una contraseña válida', () => {
  expect(contrasenaEsValida('bar123')).toBe(true)
})

test.each([
  ['bar12', 'es corta'],
  ['tapaso', 'no tiene números'],
  ['123456', 'no tiene letras'],
])('«%s» no es válida porque %s', (contrasena) => {
  expect(contrasenaEsValida(contrasena)).toBe(false)
})

test('las letras con tilde y la eñe cuentan como letras', () => {
  expect(contrasenaEsValida('ñandú7')).toBe(true)
})

test('evaluarContrasena dice qué regla se cumple y cuál falta, en orden', () => {
  expect(evaluarContrasena('abc')).toEqual([
    { id: 'largo', etiqueta: 'Mínimo 6 caracteres', cumplida: false },
    { id: 'letra', etiqueta: 'Al menos una letra', cumplida: true },
    { id: 'numero', etiqueta: 'Al menos un número', cumplida: false },
  ])
})

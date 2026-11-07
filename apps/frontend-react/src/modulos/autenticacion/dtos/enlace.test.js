import { expect, test } from 'vitest'

import { correoHaciaApi } from './correo'
import {
  enlaceDesdeParametros,
  enlaceEstaCompleto,
  enlaceHaciaApi,
  nuevaContrasenaHaciaApi,
} from './enlace'

test('enlaceDesdeParametros lee el uid y el token de la URL', () => {
  const enlace = enlaceDesdeParametros(new URLSearchParams('uid=Mg&token=dee4p4-3781ec'))

  expect(enlace).toEqual({ uid: 'Mg', token: 'dee4p4-3781ec' })
  expect(enlaceEstaCompleto(enlace)).toBe(true)
})

test('un enlace al que le falta una de las dos piezas no está completo', () => {
  expect(enlaceEstaCompleto(enlaceDesdeParametros(new URLSearchParams('uid=Mg')))).toBe(false)
  expect(enlaceEstaCompleto(enlaceDesdeParametros(new URLSearchParams('')))).toBe(false)
})

test('hacia la API van las dos piezas del enlace, y la contraseña cuando la hay', () => {
  const enlace = { uid: 'Mg', token: 'abc' }

  expect(enlaceHaciaApi(enlace)).toEqual({ uid: 'Mg', token: 'abc' })
  expect(nuevaContrasenaHaciaApi({ ...enlace, contrasena: 'bar123' })).toEqual({
    uid: 'Mg',
    token: 'abc',
    contrasena: 'bar123',
  })
})

test('correoHaciaApi manda el correo sin espacios', () => {
  expect(correoHaciaApi(' ana@bar.com ')).toEqual({ correo: 'ana@bar.com' })
})

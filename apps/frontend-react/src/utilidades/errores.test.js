import { describe, expect, test } from 'vitest'

import { errorDeApi, errorDeConexion } from '@/pruebas/erroresDeApi'

import {
  codigoDeError,
  erroresDeCampo,
  esErrorDeConexion,
  MENSAJE_POR_DEFECTO,
  MENSAJE_SIN_CONEXION,
  mensajeDeError,
} from './errores'

describe('mensajeDeError', () => {
  test('usa el mensaje que manda el backend', () => {
    const error = errorDeApi('usuario_inactivo', { mensaje: 'Esta cuenta está desactivada.' })

    expect(mensajeDeError(error)).toBe('Esta cuenta está desactivada.')
  })

  test('sin respuesta del servidor habla de la conexión', () => {
    expect(mensajeDeError(errorDeConexion())).toBe(MENSAJE_SIN_CONEXION)
  })

  test('nunca enseña el texto interno de un error que no viene de la API', () => {
    expect(mensajeDeError(new Error('TypeError: x is undefined'))).toBe(MENSAJE_POR_DEFECTO)
  })
})

test('codigoDeError devuelve el código estable del error', () => {
  expect(codigoDeError(errorDeApi('enlace_invalido'))).toBe('enlace_invalido')
})

test('un error con respuesta del servidor no es de conexión', () => {
  expect(esErrorDeConexion(errorDeApi('datos_invalidos'))).toBe(false)
  expect(esErrorDeConexion(errorDeConexion())).toBe(true)
})

test('erroresDeCampo devuelve los detalles, o un objeto vacío si no hay', () => {
  const detalles = { nombre: ['Este campo es requerido.'] }

  expect(erroresDeCampo(errorDeApi('datos_invalidos', { detalles }))).toEqual(detalles)
  expect(erroresDeCampo(errorDeApi('no_encontrado'))).toEqual({})
})

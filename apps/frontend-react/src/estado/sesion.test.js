import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import {
  borrarSesion,
  guardarSesion,
  leerRefresco,
  leerTokenDeAcceso,
  useUsuarioDeSesion,
} from './sesion'

const SESION = {
  tokenDeAcceso: 'acceso-de-prueba',
  tokenDeRefresco: 'refresco-de-prueba',
  usuario: { id: 1, nombreCompleto: 'Ana Ríos' },
}

function valoresGuardadosEnElNavegador() {
  return Array.from({ length: localStorage.length }, (_, posicion) =>
    localStorage.getItem(localStorage.key(posicion))
  )
}

// Dentro de `act`: borrar la sesión avisa a los hooks que siguen montados.
afterEach(() => act(() => borrarSesion()))

test('el refresco se guarda en localStorage y el acceso solo en memoria', () => {
  guardarSesion(SESION)

  expect(leerRefresco()).toBe('refresco-de-prueba')
  expect(leerTokenDeAcceso()).toBe('acceso-de-prueba')
  expect(valoresGuardadosEnElNavegador()).not.toContain('acceso-de-prueba')
})

test('borrar la sesión quita los dos tokens', () => {
  guardarSesion(SESION)

  borrarSesion()

  expect(leerRefresco()).toBeNull()
  expect(leerTokenDeAcceso()).toBeNull()
})

test('quien lee el usuario se entera cuando alguien inicia sesión', () => {
  const { result } = renderHook(() => useUsuarioDeSesion())
  expect(result.current).toBeNull()

  act(() => guardarSesion(SESION))

  expect(result.current).toEqual({ id: 1, nombreCompleto: 'Ana Ríos' })
})

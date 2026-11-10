import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import useFiltroPersistente from './useFiltroPersistente'

const CLAVE = 'el-tapazo:filtros:prueba'

afterEach(() => sessionStorage.removeItem(CLAVE))

test('recupera el filtro al desmontar y volver a montar la vista', () => {
  const primeraVista = renderHook(() => useFiltroPersistente('prueba', 'todos'))

  act(() => primeraVista.result.current[1]('pendiente'))
  primeraVista.unmount()

  const vistaDeRegreso = renderHook(() => useFiltroPersistente('prueba', 'todos'))

  expect(vistaDeRegreso.result.current[0]).toBe('pendiente')
})

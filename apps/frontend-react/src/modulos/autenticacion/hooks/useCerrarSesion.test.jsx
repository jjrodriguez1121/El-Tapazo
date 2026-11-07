import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { borrarSesion, guardarSesion, leerRefresco } from '@/estado/sesion'
import { errorDeConexion } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { cerrarSesion } from '../api/apiSesiones'
import { useCerrarSesion } from './useCerrarSesion'

vi.mock('../api/apiSesiones')

const SESION = {
  tokenDeAcceso: 'acceso-de-prueba',
  tokenDeRefresco: 'refresco-de-prueba',
  usuario: { id: 1, nombreCompleto: 'Ana Ríos' },
}

function BotonDeSalir() {
  const cierre = useCerrarSesion()
  return (
    <button type="button" onClick={() => cierre.mutate()}>
      Salir
    </button>
  )
}

afterEach(() => {
  vi.resetAllMocks()
  act(() => borrarSesion())
})

async function salir() {
  guardarSesion(SESION)
  const usuario = userEvent.setup()
  renderizarEnRuta(<BotonDeSalir />, '/inicio')
  await usuario.click(screen.getByRole('button', { name: 'Salir' }))
}

test('al salir anula el refresco en el servidor, borra la sesión y lleva al acceso', async () => {
  cerrarSesion.mockResolvedValue(undefined)

  await salir()

  expect(await screen.findByText('Ahora en /acceso')).toBeInTheDocument()
  expect(cerrarSesion).toHaveBeenCalledWith('refresco-de-prueba')
  expect(leerRefresco()).toBeNull()
})

test('aunque el servidor no conteste, la sesión se borra igual', async () => {
  cerrarSesion.mockRejectedValue(errorDeConexion())

  await salir()

  expect(await screen.findByText('Ahora en /acceso')).toBeInTheDocument()
  expect(leerRefresco()).toBeNull()
})

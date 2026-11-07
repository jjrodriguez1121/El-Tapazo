import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { errorDeApi } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { restablecerContrasena } from '../api/apiContrasenas'
import PaginaNuevaContrasena from './PaginaNuevaContrasena'

vi.mock('../api/apiContrasenas')

const RUTA = '/nueva-contrasena?uid=Mg&token=token-de-prueba'

afterEach(() => vi.resetAllMocks())

async function guardar(contrasena) {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaNuevaContrasena />, RUTA)
  await usuario.type(screen.getByLabelText('Tu contraseña nueva'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Guardar la contraseña' }))
}

test('un enlace incompleto dice que no es válido y ofrece pedir otro', () => {
  renderizarEnRuta(<PaginaNuevaContrasena />, '/nueva-contrasena?uid=Mg')

  expect(
    screen.getByRole('heading', { name: 'El enlace no es válido o ya venció.' })
  ).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Pedir un enlace nuevo' })).toHaveAttribute(
    'href',
    '/recuperar-contrasena'
  )
})

test('guarda la contraseña nueva con las dos piezas del enlace', async () => {
  restablecerContrasena.mockResolvedValue(undefined)

  await guardar('bar123')

  expect(
    await screen.findByRole('heading', { name: 'Tu contraseña quedó lista.' })
  ).toBeInTheDocument()
  expect(restablecerContrasena.mock.calls[0][0]).toEqual({
    uid: 'Mg',
    token: 'token-de-prueba',
    contrasena: 'bar123',
  })
})

test('si el backend dice que el enlace ya no sirve, se enseña igual que uno incompleto', async () => {
  restablecerContrasena.mockRejectedValue(errorDeApi('enlace_invalido'))

  await guardar('bar123')

  expect(
    await screen.findByRole('heading', { name: 'El enlace no es válido o ya venció.' })
  ).toBeInTheDocument()
})

test('una contraseña sin números no se envía', async () => {
  await guardar('tapaso')

  expect(screen.getByText('Esa contraseña no sirve todavía:')).toBeInTheDocument()
  expect(restablecerContrasena).not.toHaveBeenCalled()
})

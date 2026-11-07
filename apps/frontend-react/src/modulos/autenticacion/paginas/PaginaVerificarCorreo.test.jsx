import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { errorDeApi } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { confirmarVerificacion, solicitarVerificacion } from '../api/apiVerificacion'
import PaginaVerificarCorreo from './PaginaVerificarCorreo'

vi.mock('../api/apiVerificacion')

const RUTA = '/verificar-correo?uid=Mg&token=token-de-prueba'

afterEach(() => vi.resetAllMocks())

test('con el enlace comprueba sola, una sola vez, y avisa que el correo quedó verificado', async () => {
  confirmarVerificacion.mockResolvedValue(undefined)

  renderizarEnRuta(<PaginaVerificarCorreo />, RUTA)

  expect(screen.getByRole('heading', { name: 'Comprobando el enlace…' })).toBeInTheDocument()
  expect(
    await screen.findByRole('heading', { name: 'Tu correo quedó verificado.' })
  ).toBeInTheDocument()
  expect(confirmarVerificacion).toHaveBeenCalledTimes(1)
  expect(confirmarVerificacion.mock.calls[0][0]).toEqual({ uid: 'Mg', token: 'token-de-prueba' })
})

test('si el enlace ya no sirve deja pedir otro y lo reenvía', async () => {
  const usuario = userEvent.setup()
  confirmarVerificacion.mockRejectedValue(errorDeApi('enlace_invalido'))
  solicitarVerificacion.mockResolvedValue(undefined)
  renderizarEnRuta(<PaginaVerificarCorreo />, RUTA)

  await usuario.click(await screen.findByRole('button', { name: 'Pedir otro enlace' }))
  await usuario.type(screen.getByLabelText('Correo'), 'ana@bar.com')
  await usuario.click(screen.getByRole('button', { name: 'Reenviar el enlace' }))

  expect(await screen.findByRole('heading', { name: 'Revisa tu bandeja.' })).toBeInTheDocument()
  expect(solicitarVerificacion.mock.calls[0][0]).toBe('ana@bar.com')
})

test('sin enlace va directo a pedir otro, sin comprobar nada', () => {
  renderizarEnRuta(<PaginaVerificarCorreo />, '/verificar-correo')

  expect(screen.getByRole('heading', { name: 'Pide otro enlace' })).toBeInTheDocument()
  expect(confirmarVerificacion).not.toHaveBeenCalled()
})

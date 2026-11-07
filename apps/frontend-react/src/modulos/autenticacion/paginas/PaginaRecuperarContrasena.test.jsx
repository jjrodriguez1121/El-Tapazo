import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { errorDeApi } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { solicitarRecuperacion } from '../api/apiContrasenas'
import PaginaRecuperarContrasena from './PaginaRecuperarContrasena'

vi.mock('../api/apiContrasenas')

afterEach(() => vi.resetAllMocks())

async function pedirElEnlacePara(correo) {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaRecuperarContrasena />, '/recuperar-contrasena')
  await usuario.type(screen.getByLabelText('Correo'), correo)
  await usuario.click(screen.getByRole('button', { name: 'Enviarme el enlace' }))
  return usuario
}

test('con un correo mal escrito no envía nada', async () => {
  await pedirElEnlacePara('ana@bar')

  expect(screen.getByText('Ese correo no parece válido.')).toBeInTheDocument()
  expect(solicitarRecuperacion).not.toHaveBeenCalled()
})

test('después de enviar dice lo mismo exista o no el correo, y deja probar con otro', async () => {
  solicitarRecuperacion.mockResolvedValue(undefined)

  const usuario = await pedirElEnlacePara('ana@bar.com')

  expect(await screen.findByRole('heading', { name: 'Revisa tu bandeja.' })).toBeInTheDocument()
  expect(solicitarRecuperacion.mock.calls[0][0]).toBe('ana@bar.com')

  await usuario.click(screen.getByRole('button', { name: 'Enviarlo a otro correo' }))
  expect(screen.getByRole('heading', { name: 'Recupera tu contraseña' })).toBeInTheDocument()
})

test('si el backend frena por demasiadas peticiones, enseña su mensaje', async () => {
  solicitarRecuperacion.mockRejectedValue(
    errorDeApi('demasiadas_peticiones', { mensaje: 'Demasiados intentos.', estado: 429 })
  )

  await pedirElEnlacePara('ana@bar.com')

  expect(await screen.findByRole('alert')).toHaveTextContent('Demasiados intentos.')
})

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { borrarSesion, leerRefresco } from '@/estado/sesion'
import { errorDeApi, errorDeConexion } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { iniciarSesion } from '../api/apiSesiones'
import { solicitarVerificacion } from '../api/apiVerificacion'
import PaginaIniciarSesion from './PaginaIniciarSesion'

vi.mock('../api/apiSesiones')
vi.mock('../api/apiVerificacion')

const SESION = {
  tokenDeAcceso: 'acceso-de-prueba',
  tokenDeRefresco: 'refresco-de-prueba',
  usuario: { id: 1, nombreCompleto: 'Ana Ríos' },
}

afterEach(() => {
  vi.resetAllMocks()
  borrarSesion()
})

async function entrarCon(correo, contrasena) {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaIniciarSesion />, '/acceso')
  await usuario.type(screen.getByLabelText('Correo'), correo)
  await usuario.type(screen.getByLabelText('Contraseña'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Entrar' }))
  return usuario
}

test('con el formulario vacío pide los datos y no llama al backend', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaIniciarSesion />, '/acceso')

  await usuario.click(screen.getByRole('button', { name: 'Entrar' }))

  expect(screen.getByText('Escribe tu correo.')).toBeInTheDocument()
  expect(screen.getByText('Escribe tu contraseña.')).toBeInTheDocument()
  expect(iniciarSesion).not.toHaveBeenCalled()
})

test('al entrar guarda la sesión y lleva al inicio', async () => {
  iniciarSesion.mockResolvedValue(SESION)

  await entrarCon('ana@bar.com', 'bar123')

  expect(await screen.findByText('Ahora en /inicio')).toBeInTheDocument()
  expect(iniciarSesion.mock.calls[0][0]).toEqual({ correo: 'ana@bar.com', contrasena: 'bar123' })
  expect(leerRefresco()).toBe('refresco-de-prueba')
})

test('con credenciales incorrectas enseña el mensaje del backend y marca los dos campos', async () => {
  iniciarSesion.mockRejectedValue(
    errorDeApi('credenciales_invalidas', {
      mensaje: 'El correo o la contraseña no son correctos.',
      estado: 401,
    })
  )

  await entrarCon('ana@bar.com', 'no-es-esta1')

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'El correo o la contraseña no son correctos.'
  )
  expect(screen.getByLabelText('Correo')).toHaveAttribute('aria-invalid', 'true')
  expect(screen.getByLabelText('Contraseña')).toHaveAttribute('aria-invalid', 'true')
})

test('con el correo sin verificar ofrece reenviar el enlace y lo reenvía', async () => {
  iniciarSesion.mockRejectedValue(errorDeApi('correo_no_verificado', { estado: 403 }))
  solicitarVerificacion.mockResolvedValue(undefined)

  const usuario = await entrarCon('ana@bar.com', 'bar123')
  await usuario.click(await screen.findByRole('button', { name: 'Reenviar el enlace' }))

  expect(
    await screen.findByText('Te reenviamos el enlace. Revisa tu bandeja de entrada.')
  ).toBeInTheDocument()
  expect(solicitarVerificacion.mock.calls[0][0]).toBe('ana@bar.com')
})

test('sin conexión deja volver a intentar sin reescribir nada', async () => {
  iniciarSesion.mockRejectedValueOnce(errorDeConexion()).mockResolvedValueOnce(SESION)

  const usuario = await entrarCon('ana@bar.com', 'bar123')
  await usuario.click(await screen.findByRole('button', { name: 'Volver a intentar' }))

  expect(await screen.findByText('Ahora en /inicio')).toBeInTheDocument()
})

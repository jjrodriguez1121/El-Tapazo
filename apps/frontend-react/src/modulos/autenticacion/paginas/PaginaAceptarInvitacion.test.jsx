import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { borrarSesion } from '@/estado/sesion'
import { errorDeApi } from '@/pruebas/erroresDeApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import { aceptarInvitacion, obtenerInvitacionPendiente } from '../api/apiInvitaciones'
import PaginaAceptarInvitacion from './PaginaAceptarInvitacion'

vi.mock('../api/apiInvitaciones')

const RUTA = '/invitacion?token=token-de-prueba'

const INVITACION = {
  correo: 'luis@bar.com',
  rol: 'mesero',
  negocio: 'Bar El Tapaso',
  expiraEn: '2026-09-18T15:19:18-05:00',
}

afterEach(() => {
  vi.resetAllMocks()
  borrarSesion()
})

async function llenarElFormulario({ contrasena }) {
  const usuario = userEvent.setup()
  obtenerInvitacionPendiente.mockResolvedValue(INVITACION)
  renderizarEnRuta(<PaginaAceptarInvitacion />, RUTA)
  await screen.findByRole('heading', { name: 'Te invitaron a Bar El Tapaso' })

  await usuario.type(screen.getByLabelText('Nombre'), 'Luis')
  await usuario.type(screen.getByLabelText('Apellido'), 'Pérez')
  await usuario.type(screen.getByLabelText('Tu contraseña nueva'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Crear mi cuenta' }))
}

test('mientras busca la invitación enseña el esqueleto, y después de qué es', async () => {
  obtenerInvitacionPendiente.mockResolvedValue(INVITACION)

  renderizarEnRuta(<PaginaAceptarInvitacion />, RUTA)

  expect(screen.getByText('Buscando tu invitación…')).toBeInTheDocument()
  expect(
    await screen.findByRole('heading', { name: 'Te invitaron a Bar El Tapaso' })
  ).toBeInTheDocument()
  expect(screen.getByText('luis@bar.com')).toBeInTheDocument()
  expect(screen.getByText('Mesero')).toBeInTheDocument()
  expect(obtenerInvitacionPendiente).toHaveBeenCalledWith('token-de-prueba')
})

test('un enlace sin token dice que la invitación no existe, sin preguntarle al backend', () => {
  renderizarEnRuta(<PaginaAceptarInvitacion />, '/invitacion')

  expect(screen.getByRole('heading', { name: 'Esa invitación no existe.' })).toBeInTheDocument()
  expect(obtenerInvitacionPendiente).not.toHaveBeenCalled()
})

test('una invitación vencida lo dice y lleva a iniciar sesión', async () => {
  obtenerInvitacionPendiente.mockRejectedValue(errorDeApi('invitacion_vencida', { estado: 409 }))

  renderizarEnRuta(<PaginaAceptarInvitacion />, RUTA)

  expect(await screen.findByRole('heading', { name: 'La invitación venció.' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Ir a iniciar sesión' })).toHaveAttribute(
    'href',
    '/acceso'
  )
})

test('una contraseña que no cumple las reglas no se envía y las marca en rojo', async () => {
  await llenarElFormulario({ contrasena: 'tapaso' })

  expect(screen.getByText('Esa contraseña no sirve todavía:')).toBeInTheDocument()
  expect(aceptarInvitacion).not.toHaveBeenCalled()
})

test('con los datos bien crea la cuenta y entra directo, sin pasar por el login', async () => {
  aceptarInvitacion.mockResolvedValue({
    tokenDeAcceso: 'acceso-de-prueba',
    tokenDeRefresco: 'refresco-de-prueba',
    usuario: { id: 2, nombreCompleto: 'Luis Pérez' },
  })

  await llenarElFormulario({ contrasena: 'bar123' })

  expect(await screen.findByText('Ahora en /inicio')).toBeInTheDocument()
  expect(aceptarInvitacion.mock.calls[0][0]).toEqual({
    token: 'token-de-prueba',
    nombre: 'Luis',
    apellido: 'Pérez',
    telefono: '',
    contrasena: 'bar123',
  })
})

import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { borrarSesion, guardarSesion } from '@/estado/sesion'
import { cerrarSesion } from '@/modulos/autenticacion/api/apiSesiones'
import { renderizarEnRuta } from '@/pruebas/renderizar'

import PlantillaPrincipal from './PlantillaPrincipal'

vi.mock('@/modulos/autenticacion/api/apiSesiones')

const ADMINISTRADORA = {
  id: 1,
  nombreCompleto: 'Ana Ríos',
  rol: 'admin',
  esAdministrador: true,
  negocio: { id: 3, nombreComercial: 'Bar La Esquina' },
}

afterEach(() => {
  vi.resetAllMocks()
  act(() => borrarSesion())
})

function entrarComo(usuario) {
  guardarSesion({ tokenDeAcceso: 'acceso', tokenDeRefresco: 'refresco', usuario })
  renderizarEnRuta(<PlantillaPrincipal />, '/inicio')
}

test('el menú lleva el nombre del negocio y la barra dice quién entró', () => {
  entrarComo(ADMINISTRADORA)

  expect(screen.getByText('Bar La Esquina')).toBeInTheDocument()
  expect(screen.queryByText('El Tapaso')).not.toBeInTheDocument()
  expect(screen.getByText('Ana Ríos')).toBeInTheDocument()
  expect(screen.getByText('Administrador')).toBeInTheDocument()
})

test('a un mesero no le aparecen las secciones del administrador', () => {
  entrarComo({
    ...ADMINISTRADORA,
    nombreCompleto: 'Luis Pérez',
    rol: 'mesero',
    esAdministrador: false,
  })

  expect(screen.getByRole('link', { name: 'Cuentas' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Productos' })).not.toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Configuración' })).not.toBeInTheDocument()
})

test('«Salir» cierra la sesión y lleva al acceso', async () => {
  cerrarSesion.mockResolvedValue(undefined)
  const usuario = userEvent.setup()
  entrarComo(ADMINISTRADORA)

  await usuario.click(screen.getByRole('button', { name: 'Salir' }))

  expect(await screen.findByText('Ahora en /acceso')).toBeInTheDocument()
  expect(cerrarSesion).toHaveBeenCalledWith('refresco')
})

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaProveedores from './PaginaProveedores'

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: {
    get: vi.fn(async () => ({
      data: [
        { id: 1, razon_social: 'Bavaria S.A.', nit: '', nombre_contacto: '', cantidadProductos: 0 },
        { id: 2, razon_social: 'Postobón S.A.', nit: '', nombre_contacto: '', cantidadProductos: 0 },
        { id: 3, razon_social: 'Coca-Cola FEMSA', nit: '', nombre_contacto: '', cantidadProductos: 0 },
      ],
    })),
    post: vi.fn(async (_ruta, datos) => ({
      data: {
        id: 4,
        ...datos,
        activo: true,
      },
    })),
    put: vi.fn(async (ruta, datos) => ({
      data: {
        id: Number(ruta.match(/(\d+)/)?.[1]),
        ...datos,
        activo: true,
      },
    })),
  },
}))

test('muestra los proveedores de ejemplo', async () => {
  renderizarEnRuta(<PaginaProveedores />, '/proveedores')

  expect(screen.getByRole('heading', { name: 'Proveedores' })).toBeInTheDocument()
  expect(await screen.findByText('Bavaria S.A.')).toBeInTheDocument()
  expect(screen.getByText('Postobón S.A.')).toBeInTheDocument()
  expect(screen.getByText('Coca-Cola FEMSA')).toBeInTheDocument()
})

test('agrega un proveedor al listado sin usar el backend', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaProveedores />, '/proveedores')

  await usuario.click(screen.getByRole('button', { name: 'Nuevo proveedor' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Razón social' }), 'Distribuidora local')
  await usuario.click(screen.getByRole('button', { name: 'Guardar proveedor' }))

  expect(await screen.findByText('Distribuidora local')).toBeInTheDocument()
  expect(screen.getAllByText('0 productos')).toHaveLength(4)
})

test('impide repetir razón social y valida correo inválido', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaProveedores />, '/proveedores')

  await usuario.click(screen.getByRole('button', { name: 'Nuevo proveedor' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Razón social' }), 'Bavaria S.A.')
  await usuario.click(screen.getByRole('button', { name: 'Guardar proveedor' }))
  expect(screen.getByText('Ya existe un proveedor con esa razón social.')).toBeInTheDocument()

  await usuario.clear(screen.getByRole('textbox', { name: 'Razón social' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Razón social' }), 'Proveedor Nuevo')
  await usuario.type(screen.getByRole('textbox', { name: 'Correo' }), 'correo-mal')
  await usuario.click(screen.getByRole('button', { name: 'Guardar proveedor' }))
  expect(screen.getByText('Ese correo no parece válido.')).toBeInTheDocument()
})

test('edita y desactiva un proveedor desde sus acciones', async () => {
  const usuario = userEvent.setup()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  renderizarEnRuta(<PaginaProveedores />, '/proveedores')

  await usuario.click(await screen.findByRole('button', { name: 'Editar Bavaria S.A.' }))
  const razonSocial = screen.getByRole('textbox', { name: 'Razón social' })
  await usuario.clear(razonSocial)
  await usuario.type(razonSocial, 'Bavaria Editada')
  await usuario.click(screen.getByRole('button', { name: 'Guardar proveedor' }))
  expect(await screen.findByText('Bavaria Editada')).toBeInTheDocument()

  await usuario.click(screen.getByRole('button', { name: 'Eliminar Bavaria Editada' }))
  expect(await screen.findByText('Postobón S.A.')).toBeInTheDocument()
  expect(screen.queryByText('Bavaria Editada')).not.toBeInTheDocument()
})
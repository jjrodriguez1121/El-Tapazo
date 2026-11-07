import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaProveedores from './PaginaProveedores'

test('muestra los proveedores de ejemplo', () => {
  renderizarEnRuta(<PaginaProveedores />, '/proveedores')

  expect(screen.getByRole('heading', { name: 'Proveedores' })).toBeInTheDocument()
  expect(screen.getByText('Bavaria S.A.')).toBeInTheDocument()
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
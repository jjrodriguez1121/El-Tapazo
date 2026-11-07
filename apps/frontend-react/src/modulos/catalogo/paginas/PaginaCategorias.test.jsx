import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { crearCategoria } from '../api/apiCategorias'

import PaginaCategorias from './PaginaCategorias'

vi.mock('../api/apiCategorias', () => ({ crearCategoria: vi.fn() }))

beforeEach(() => {
  crearCategoria.mockReset()
})

test('renderiza el título y el botón de nueva categoría', () => {
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  expect(screen.getByRole('heading', { name: 'Categorías' })).toBeInTheDocument()
  expect(
    screen.getByText('Organización del catálogo de productos')
  ).toBeInTheDocument()
  expect(
    screen.getByRole('button', { name: /Nueva categoría/i })
  ).toBeInTheDocument()
})

test('muestra las tarjetas de categorías con sus nombres y cantidades de productos', () => {
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  expect(screen.getByText('Cervezas')).toBeInTheDocument()
  expect(screen.getByText('13 productos')).toBeInTheDocument()

  expect(screen.getByText('Gaseosas')).toBeInTheDocument()
  expect(screen.getByText('12 productos')).toBeInTheDocument()

  expect(screen.getByText('Energizantes')).toBeInTheDocument()
  expect(screen.getByText('Aguas')).toBeInTheDocument()
  expect(screen.getByText('Ron')).toBeInTheDocument()
  expect(screen.getAllByText('6 productos')).toHaveLength(3)

  expect(screen.getByText('Aguardientes')).toBeInTheDocument()
  expect(screen.getByText('7 productos')).toBeInTheDocument()
})

test('crea una categoría desde el formulario y la agrega al listado', async () => {
  const usuario = userEvent.setup()
  crearCategoria.mockResolvedValue({ id: 50, nombre: 'Cócteles', descripcion: '' })
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  await usuario.click(screen.getByRole('button', { name: /Nueva categoría/i }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre' }), 'Cócteles')
  await usuario.click(screen.getByRole('button', { name: 'Crear categoría' }))

  await waitFor(() =>
    expect(crearCategoria).toHaveBeenCalledWith({ nombre: 'Cócteles', descripcion: '' })
  )
  expect(await screen.findByText('Cócteles')).toBeInTheDocument()
  expect(screen.getByText('0 productos')).toBeInTheDocument()
})

test('impide crear una categoría duplicada', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  await usuario.click(screen.getByRole('button', { name: /Nueva categoría/i }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre' }), '  cervezas  ')
  await usuario.click(screen.getByRole('button', { name: 'Crear categoría' }))

  expect(screen.getByText('Ya existe una categoría con ese nombre.')).toBeInTheDocument()
  expect(crearCategoria).not.toHaveBeenCalled()
})

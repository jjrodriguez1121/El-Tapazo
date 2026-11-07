import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { actualizarCategoria, crearCategoria, desactivarCategoria } from '../api/apiCategorias'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

import PaginaCategorias from './PaginaCategorias'

vi.mock('../api/apiCategorias', () => ({
  crearCategoria: vi.fn(),
  actualizarCategoria: vi.fn(),
  desactivarCategoria: vi.fn(),
}))
vi.mock('../hooks/useCatalogoDeProductos', () => ({
  CLAVE_CATALOGO_PRODUCTOS: ['catalogo', 'productos'],
  useCatalogoDeProductos: vi.fn(),
}))

beforeEach(() => {
  crearCategoria.mockReset()
  actualizarCategoria.mockReset()
  desactivarCategoria.mockReset()
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    data: {
      categorias: [
        { id: 1, nombre: 'Cervezas', cantidadProductos: 13 },
        { id: 2, nombre: 'Gaseosas', cantidadProductos: 12 },
        { id: 3, nombre: 'Energizantes', cantidadProductos: 6 },
        { id: 4, nombre: 'Aguas', cantidadProductos: 6 },
        { id: 5, nombre: 'Ron', cantidadProductos: 6 },
        { id: 6, nombre: 'Aguardientes', cantidadProductos: 7 },
      ],
    },
  })
})

test('renderiza el título y el botón de nueva categoría', async () => {
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  expect(await screen.findByRole('heading', { name: 'Categorías' })).toBeInTheDocument()
  expect(
    screen.getByText('Organización del catálogo de productos')
  ).toBeInTheDocument()
  expect(
    screen.getByRole('button', { name: /Nueva categoría/i })
  ).toBeInTheDocument()
})

test('muestra las tarjetas de categorías con sus nombres y cantidades de productos', async () => {
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  expect(await screen.findByText('Cervezas')).toBeInTheDocument()
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

  await usuario.click(await screen.findByRole('button', { name: /Nueva categoría/i }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre' }), 'Cócteles')
  await usuario.click(screen.getByRole('button', { name: 'Crear categoría' }))

  await waitFor(() =>
    expect(crearCategoria.mock.calls[0][0]).toEqual({ nombre: 'Cócteles', descripcion: '' })
  )
})

test('impide crear una categoría duplicada', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  await usuario.click(await screen.findByRole('button', { name: /Nueva categoría/i }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre' }), '  cervezas  ')
  await usuario.click(screen.getByRole('button', { name: 'Crear categoría' }))

  expect(screen.getByText('Ya existe una categoría con ese nombre.')).toBeInTheDocument()
  expect(crearCategoria).not.toHaveBeenCalled()
})

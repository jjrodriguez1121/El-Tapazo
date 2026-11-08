import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import {
  activarCategoria,
  actualizarCategoria,
  crearCategoria,
  desactivarCategoria,
} from '../api/apiCategorias'
import { obtenerCatalogoDeProductos, obtenerTodasLasCategorias } from '../api/apiListaProductos'

import PaginaCategorias from './PaginaCategorias'

vi.mock('../api/apiCategorias', () => ({
  crearCategoria: vi.fn(),
  actualizarCategoria: vi.fn(),
  desactivarCategoria: vi.fn(),
  activarCategoria: vi.fn(),
}))
vi.mock('../api/apiListaProductos', () => ({
  obtenerCatalogoDeProductos: vi.fn(),
  obtenerTodasLasCategorias: vi.fn(),
}))

beforeEach(() => {
  crearCategoria.mockReset()
  actualizarCategoria.mockReset()
  desactivarCategoria.mockReset()
  activarCategoria.mockReset()
  obtenerCatalogoDeProductos.mockResolvedValue({
    productos: [
      ...Array.from({ length: 13 }, (_, indice) => ({ id: indice, categoria: { id: 1 } })),
      ...Array.from({ length: 12 }, (_, indice) => ({ id: indice + 13, categoria: { id: 2 } })),
      ...Array.from({ length: 6 }, (_, indice) => ({ id: indice + 25, categoria: { id: 3 } })),
      ...Array.from({ length: 6 }, (_, indice) => ({ id: indice + 31, categoria: { id: 4 } })),
      ...Array.from({ length: 6 }, (_, indice) => ({ id: indice + 37, categoria: { id: 5 } })),
      ...Array.from({ length: 7 }, (_, indice) => ({ id: indice + 43, categoria: { id: 6 } })),
    ],
  })
  obtenerTodasLasCategorias.mockResolvedValue([
    { id: 1, nombre: 'Cervezas', activa: true },
    { id: 2, nombre: 'Gaseosas', activa: true },
    { id: 3, nombre: 'Energizantes', activa: true },
    { id: 4, nombre: 'Aguas', activa: true },
    { id: 5, nombre: 'Ron', activa: true },
    { id: 6, nombre: 'Aguardientes', activa: true },
  ])
  desactivarCategoria.mockImplementation(async (id) => ({
    id,
    activa: false,
  }))
  activarCategoria.mockImplementation(async (id) => ({
    id,
    activa: true,
  }))
})

afterEach(() => vi.restoreAllMocks())

test('renderiza el título y el botón de nueva categoría', async () => {
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  expect(await screen.findByRole('heading', { name: 'Categorías' })).toBeInTheDocument()
  expect(screen.getByText('Organización del catálogo de productos')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Nueva categoría/i })).toBeInTheDocument()
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

test('desactiva y reactiva una categoría sin quitar sus productos', async () => {
  const usuario = userEvent.setup()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  renderizarEnRuta(<PaginaCategorias />, '/categorias')

  await usuario.click(await screen.findByRole('button', { name: 'Desactivar Cervezas' }))
  expect(desactivarCategoria).toHaveBeenCalledWith(1)

  await usuario.selectOptions(
    screen.getByRole('combobox', { name: 'Estado de las categorías' }),
    'inactivas'
  )
  expect(await screen.findByText('Cervezas')).toBeInTheDocument()
  expect(screen.getByText('Inactiva')).toBeInTheDocument()
  expect(screen.getByText('13 productos')).toBeInTheDocument()

  await usuario.click(screen.getByRole('button', { name: 'Activar Cervezas' }))
  expect(activarCategoria).toHaveBeenCalledWith(1)
  await usuario.selectOptions(
    screen.getByRole('combobox', { name: 'Estado de las categorías' }),
    'activas'
  )
  expect(await screen.findByText('Cervezas')).toBeInTheDocument()
})

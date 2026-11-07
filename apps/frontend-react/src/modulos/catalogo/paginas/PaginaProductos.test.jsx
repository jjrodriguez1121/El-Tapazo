import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

import PaginaProductos from './PaginaProductos'

vi.mock('../hooks/useCatalogoDeProductos', () => ({
  useCatalogoDeProductos: vi.fn(),
}))

beforeEach(() => {
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    data: {
      categorias: [
        { id: 1, nombre: 'Bebidas' },
        { id: 2, nombre: 'Snacks' },
      ],
      productos: [
        {
          id: 10,
          nombre: 'Agua mineral',
          sku: 'AGU-001',
          categoria: { id: 1, nombre: 'Bebidas' },
          precio_evento: '2500.00',
        },
        {
          id: 11,
          nombre: 'Papas',
          sku: 'SNK-001',
          categoria: { id: 2, nombre: 'Snacks' },
          precio_evento: '1800.00',
        },
      ],
      existencias: [
        {
          producto: { id: 10 },
          ubicacion: { nombre: 'Bodega A-1' },
          cantidad_disponible: '12.00',
          esta_bajo_minimo: false,
        },
      ],
    },
  })
})

test('muestra productos, precios y estado de existencias', () => {
  renderizarEnRuta(<PaginaProductos />, '/productos')

  expect(screen.getByRole('heading', { name: 'Productos' })).toBeInTheDocument()
  expect(screen.getByText('Agua mineral')).toBeInTheDocument()
  expect(screen.getByText('$2.500')).toBeInTheDocument()
  expect(screen.getByText('En stock')).toBeInTheDocument()
  expect(screen.getByText('Sin stock')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Ver producto Agua mineral' })).toHaveAttribute(
    'href',
    '/productos/10'
  )
})

test('filtra productos por categoría', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaProductos />, '/productos')

  await usuario.click(screen.getByRole('button', { name: 'Bebidas' }))

  expect(screen.getByText('Agua mineral')).toBeInTheDocument()
  expect(screen.queryByText('Papas')).not.toBeInTheDocument()
})

test('informa que los productos nuevos se registran desde Compras cuando el catálogo está vacío', () => {
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    data: { categorias: [], productos: [], existencias: [] },
  })
  renderizarEnRuta(<PaginaProductos />, '/productos')

  expect(screen.getByText('Altas registradas desde Compras')).toBeInTheDocument()
  expect(screen.getByText('No hay productos para mostrar.')).toBeInTheDocument()
})
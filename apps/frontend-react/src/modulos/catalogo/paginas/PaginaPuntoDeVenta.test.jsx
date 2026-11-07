import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

import PaginaPuntoDeVenta from './PaginaPuntoDeVenta'

vi.mock('../hooks/useCatalogoDeProductos', () => ({
  useCatalogoDeProductos: vi.fn(),
}))

beforeEach(() => {
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    data: {
      productos: [
        {
          id: 10,
          nombre: 'Bujía NGK',
          sku: 'ELC-003',
          categoria: { id: 1, nombre: 'Eléctrico' },
          precio_evento: '12000.00',
        },
      ],
      categorias: [{ id: 1, nombre: 'Eléctrico' }],
      existencias: [
        {
          producto: { id: 10 },
          ubicacion: { nombre: 'Bodega C-01' },
          cantidad_disponible: '12.00',
          esta_bajo_minimo: false,
        },
      ],
    },
  })
})

test('lista los productos disponibles y filtra por categoría', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  expect(screen.getByRole('heading', { name: 'Punto de venta' })).toBeInTheDocument()
  expect(screen.getByText('Bujía NGK')).toBeInTheDocument()
  await usuario.click(screen.getByRole('button', { name: 'Eléctrico' }))
  expect(screen.getByText('Bujía NGK')).toBeInTheDocument()
})

test('agrega productos, cambia cantidades y calcula los totales', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  await usuario.click(screen.getByRole('button', { name: 'Sumar Bujía NGK' }))

  expect(screen.getByText('2 artículos')).toBeInTheDocument()
  expect(screen.getByText('$24.000')).toBeInTheDocument()
  expect(screen.getByText('$4.560')).toBeInTheDocument()
  expect(screen.getByText('$1.200')).toBeInTheDocument()
  expect(screen.getByText('$27.360')).toBeInTheDocument()
})

test('muestra eliminar siempre y retira la línea completa del carrito', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  expect(screen.getByRole('button', { name: 'Eliminar Bujía NGK del carrito' })).toBeInTheDocument()

  await usuario.click(screen.getByRole('button', { name: 'Eliminar Bujía NGK del carrito' }))

  expect(screen.getByText('El carrito está vacío')).toBeInTheDocument()
})
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, test, vi } from 'vitest'

import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

import PaginaDetalleProducto from './PaginaDetalleProducto'

vi.mock('../hooks/useCatalogoDeProductos', () => ({
  useCatalogoDeProductos: vi.fn(),
}))

beforeEach(() => {
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    data: { productos: [], categorias: [], existencias: [] },
  })
})

test('muestra la ficha del producto de ejemplo con proveedor y movimientos', () => {
  const clienteConsultas = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  render(
    <QueryClientProvider client={clienteConsultas}>
      <MemoryRouter initialEntries={['/productos/101']}>
        <Routes>
          <Route path="/productos/:productoId" element={<PaginaDetalleProducto />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )

  expect(screen.getByRole('heading', { name: 'Águila' })).toBeInTheDocument()
  expect(screen.getByText('Stock disponible')).toBeInTheDocument()
  expect(screen.getByText('Bavaria S.A.')).toBeInTheDocument()
  expect(screen.getByText('Entrada por compra')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Volver a productos/ })).toHaveAttribute(
    'href',
    '/productos'
  )
})

test('abre el mismo formulario precargado y actualiza la ficha localmente', async () => {
  const usuario = userEvent.setup()
  const clienteConsultas = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  render(
    <QueryClientProvider client={clienteConsultas}>
      <MemoryRouter initialEntries={['/productos/101']}>
        <Routes>
          <Route path="/productos/:productoId" element={<PaginaDetalleProducto />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )

  await usuario.click(screen.getByRole('button', { name: 'Editar producto' }))
  expect(screen.getByRole('heading', { name: 'Editar producto' })).toBeInTheDocument()
  expect(screen.getByRole('textbox', { name: 'Nombre del repuesto' })).toHaveValue('Águila')
  expect(screen.getByRole('textbox', { name: 'Código / SKU' })).toHaveValue('CER-001')

  await usuario.clear(screen.getByRole('textbox', { name: 'Nombre del repuesto' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre del repuesto' }), 'Águila Especial')
  await usuario.clear(screen.getByRole('spinbutton', { name: 'Precio de venta' }))
  await usuario.type(screen.getByRole('spinbutton', { name: 'Precio de venta' }), '7200')
  await usuario.click(screen.getByRole('button', { name: 'Guardar cambios' }))

  expect(screen.getByRole('heading', { name: 'Águila Especial' })).toBeInTheDocument()
  expect(screen.getByText('$7.200')).toBeInTheDocument()
})
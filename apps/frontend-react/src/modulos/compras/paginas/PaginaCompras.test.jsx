import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { clienteApi } from '@/librerias/clienteApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'
import { listarMetodosPago } from '@/modulos/ventas/api/apiVentas'
import { listarCompras } from '../api/apiCompras'

import PaginaCompras from './PaginaCompras'

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: {
    get: vi.fn(),
  },
}))

vi.mock('../api/apiCompras', () => ({
  crearCompra: vi.fn(),
  listarCompras: vi.fn(),
}))

vi.mock('@/modulos/ventas/api/apiVentas', () => ({
  listarMetodosPago: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
  listarCompras.mockResolvedValue([])
  listarMetodosPago.mockResolvedValue([{ id: 1, nombre: 'Efectivo' }])
  clienteApi.get.mockImplementation((ruta, configuracion) => {
    if (ruta === '/catalogo/proveedores/?activo=true') {
      return Promise.resolve({
        data: [
          { id: 7, razon_social: 'Proveedor A' },
          { id: 8, razon_social: 'Proveedor B' },
        ],
      })
    }
    if (ruta === '/catalogo/categorias/?activa=true' || ruta === '/catalogo/impuestos/') {
      return Promise.resolve({ data: [] })
    }
    if (ruta === '/catalogo/productos/') {
      const { page, proveedor_id: proveedorId } = configuracion.params
      if (proveedorId === '7' && page === 1) {
        return Promise.resolve({
          data: {
            results: [{ id: 11, sku: 'A-001', nombre: 'Producto proveedor A' }],
            next: '?page=2',
          },
        })
      }
      if (proveedorId === '7' && page === 2) {
        return Promise.resolve({
          data: {
            results: [{ id: 12, sku: 'A-002', nombre: 'Producto en página 2' }],
            next: null,
          },
        })
      }
      return Promise.resolve({
        data: {
          results: [{ id: 21, sku: 'B-001', nombre: 'Producto proveedor B' }],
          next: null,
        },
      })
    }
    return Promise.resolve({ data: [] })
  })
})

test('filtra los productos existentes por proveedor y carga todas las páginas', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaCompras />, '/compras')

  await usuario.selectOptions(await screen.findByLabelText('Proveedor'), '7')

  const selectorProducto = await screen.findByLabelText('Producto')
  expect(selectorProducto).toHaveTextContent('Producto proveedor A')
  expect(selectorProducto).toHaveTextContent('Producto en página 2')
  expect(selectorProducto).not.toHaveTextContent('Producto proveedor B')
  expect(clienteApi.get).toHaveBeenCalledWith('/catalogo/productos/', {
    params: { activo: true, proveedor_id: '7', page: 1 },
  })
  expect(clienteApi.get).toHaveBeenCalledWith('/catalogo/productos/', {
    params: { activo: true, proveedor_id: '7', page: 2 },
  })

  await usuario.selectOptions(screen.getByLabelText('Proveedor'), '8')
  await waitFor(() => {
    expect(screen.getByLabelText('Producto')).toHaveTextContent('Producto proveedor B')
  })
  expect(screen.getByLabelText('Producto')).not.toHaveTextContent('Producto proveedor A')
})

import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'
import { crearVenta, listarMetodosPago, obtenerDetalleVenta } from '@/modulos/ventas/api/apiVentas'

import PaginaPuntoDeVenta from './PaginaPuntoDeVenta'

vi.mock('../hooks/useCatalogoDeProductos', () => ({
  useCatalogoDeProductos: vi.fn(),
}))

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

vi.mock('@/modulos/ventas/api/apiVentas', () => ({
  crearVenta: vi.fn(),
  listarMetodosPago: vi.fn(),
  obtenerDetalleVenta: vi.fn(),
}))

beforeEach(() => {
  crearVenta.mockReset()
  listarMetodosPago.mockReset().mockResolvedValue([{ id: 1, nombre: 'Efectivo' }])
  obtenerDetalleVenta.mockReset()
  useCatalogoDeProductos.mockReturnValue({
    isPending: false,
    isError: false,
    refetch: vi.fn().mockResolvedValue({}),
    data: {
      productos: [
        {
          id: 10,
          nombre: 'Bujía NGK',
          sku: 'ELC-003',
          categoria: { id: 1, nombre: 'Eléctrico' },
          precio_evento: '12000.00',
          impuesto: { id: 1, nombre: 'IVA 19 %', porcentaje: '19.00' },
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
  expect(screen.getByText('$19.160')).toBeInTheDocument()
  expect(screen.getByText('$3.640')).toBeInTheDocument()
  expect(screen.getByText('$1.200')).toBeInTheDocument()
  expect(screen.getByText('$22.800')).toBeInTheDocument()
})

test('muestra eliminar siempre y retira la línea completa del carrito', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  expect(screen.getByRole('button', { name: 'Eliminar Bujía NGK del carrito' })).toBeInTheDocument()

  await usuario.click(screen.getByRole('button', { name: 'Eliminar Bujía NGK del carrito' }))

  expect(screen.getByText('El carrito está vacío')).toBeInTheDocument()
})

test('al registrar una venta ofrece imprimir o guardar el comprobante en PDF', async () => {
  const usuario = userEvent.setup()
  crearVenta.mockResolvedValue({
    id: 25,
    numero_venta: 'VEN-0025',
    total: '12000.00',
  })
  obtenerDetalleVenta.mockResolvedValue({
    id: 25,
    numero_venta: 'VEN-0025',
    cliente_nombre: 'Cliente general / Mostrador',
    fecha_venta: '2026-11-08T15:00:00Z',
    tipo_pago: 'contado',
    estado_entrega: 'pendiente_entrega',
    subtotal: '10084.03',
    descuento: '600.00',
    total_iva: '1915.97',
    total: '12000.00',
    detalles: [
      {
        id: 1,
        producto: 'Bujía NGK',
        sku: 'ELC-003',
        cantidad: '1.00',
        precio_unitario: '12000.00',
        subtotal: '12000.00',
      },
    ],
  })
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  await usuario.click(screen.getByRole('button', { name: 'Finalizar Venta' }))

  await waitFor(() => expect(obtenerDetalleVenta).toHaveBeenCalledWith(25))
  expect(await screen.findByText(/Venta VEN-0025 registrada correctamente/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Imprimir / Guardar PDF' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Ahora no' })).toBeInTheDocument()
})

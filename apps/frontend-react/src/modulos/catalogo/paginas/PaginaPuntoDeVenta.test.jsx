import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, test, vi } from 'vitest'

import { clienteApi } from '@/librerias/clienteApi'
import { renderizarEnRuta } from '@/pruebas/renderizar'
import { obtenerFechaMinimaVencimiento } from '@/utilidades/fechas'

import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'
import { crearVenta, listarMetodosPago, obtenerDetalleVenta } from '@/modulos/ventas/api/apiVentas'

import PaginaPuntoDeVenta from './PaginaPuntoDeVenta'

vi.mock('../hooks/useCatalogoDeProductos', () => ({
  useCatalogoDeProductos: vi.fn(),
}))

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
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
  clienteApi.get.mockReset().mockResolvedValue({ data: [] })
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
        {
          id: 11,
          nombre: 'Filtro de aceite',
          sku: 'MOT-001',
          categoria: { id: 1, nombre: 'Eléctrico' },
          precio_evento: '8000.00',
        },
        {
          id: 13,
          nombre: 'Batería descargada',
          sku: 'BAT-001',
          categoria: { id: 1, nombre: 'Eléctrico' },
          precio_evento: '50000.00',
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
        {
          producto: { id: 11 },
          ubicacion: { nombre: 'Bodega C-01' },
          cantidad_disponible: '0.00',
          esta_bajo_minimo: true,
        },
      ],
    },
  })
})

test('no ofrece clientes inactivos en el selector de venta', async () => {
  clienteApi.get.mockResolvedValue({
    data: [
      { id: 1, nombre: 'Cliente', apellido: 'Activo', activo: true },
      { id: 2, nombre: 'Cliente', apellido: 'Inactivo', activo: false },
    ],
  })

  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  expect(await screen.findByRole('option', { name: 'Cliente Activo' })).toBeInTheDocument()
  expect(screen.queryByRole('option', { name: 'Cliente Inactivo' })).not.toBeInTheDocument()
  expect(clienteApi.get).toHaveBeenCalledWith('/clientes/', { params: { activo: true } })
})

test('lista los productos disponibles y filtra por categoría', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  expect(screen.getByRole('heading', { name: 'Punto de venta' })).toBeInTheDocument()
  expect(screen.getByText('Bujía NGK')).toBeInTheDocument()
  expect(screen.queryByText('Filtro de aceite')).not.toBeInTheDocument()
  expect(screen.queryByText('Batería descargada')).not.toBeInTheDocument()
  await usuario.click(screen.getByRole('button', { name: 'Eléctrico' }))
  expect(screen.getByText('Bujía NGK')).toBeInTheDocument()
})

test('conserva el carrito al salir y volver a la vista de punto de venta', async () => {
  const usuario = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/punto-de-venta']}>
      <Routes>
        <Route
          path="/punto-de-venta"
          element={
            <>
              <PaginaPuntoDeVenta />
              <Link to="/otra-vista">Cambiar de vista</Link>
            </>
          }
        />
        <Route
          path="/otra-vista"
          element={<Link to="/punto-de-venta">Volver al punto de venta</Link>}
        />
      </Routes>
    </MemoryRouter>
  )

  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  expect(screen.getByText('1 artículo')).toBeInTheDocument()

  await usuario.click(screen.getByRole('link', { name: 'Cambiar de vista' }))
  await usuario.click(screen.getByRole('link', { name: 'Volver al punto de venta' }))

  expect(await screen.findByText('1 artículo')).toBeInTheDocument()
  expect(screen.getByText('Bujía NGK')).toBeInTheDocument()
})

test('busca productos disponibles por nombre o código', async () => {
  const usuario = userEvent.setup()
  const catalogo = useCatalogoDeProductos()
  useCatalogoDeProductos.mockReturnValue({
    ...catalogo,
    data: {
      ...catalogo.data,
      productos: [
        ...catalogo.data.productos,
        {
          id: 12,
          nombre: 'Aceite sintético',
          sku: 'LUB-001',
          categoria: { id: 2, nombre: 'Lubricantes' },
          precio_evento: '25000.00',
        },
      ],
      existencias: [
        ...catalogo.data.existencias,
        {
          producto: { id: 12 },
          ubicacion: { nombre: 'Bodega C-01' },
          cantidad_disponible: '3.00',
          esta_bajo_minimo: false,
        },
      ],
    },
  })
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.type(screen.getByRole('searchbox', { name: 'Buscar productos' }), 'lub-001')

  expect(screen.getByText('Aceite sintético')).toBeInTheDocument()
  expect(screen.queryByText('Bujía NGK')).not.toBeInTheDocument()
  expect(screen.queryByText('Filtro de aceite')).not.toBeInTheDocument()

  const buscador = screen.getByRole('searchbox', { name: 'Buscar productos' })
  await usuario.clear(buscador)
  await usuario.type(buscador, 'Aceite sintético')

  expect(screen.getByText('Aceite sintético')).toBeInTheDocument()
  expect(screen.queryByText('Bujía NGK')).not.toBeInTheDocument()
})

test('el vencimiento de una venta a crédito empieza mañana', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  await usuario.selectOptions(screen.getByLabelText('Tipo de pago'), 'credito')

  expect(screen.getByLabelText('Vencimiento')).toHaveAttribute(
    'min',
    obtenerFechaMinimaVencimiento()
  )
})

test('agrega productos, cambia cantidades y calcula los totales', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPuntoDeVenta />, '/punto-de-venta')

  expect(screen.getByRole('spinbutton', { name: 'Descuento porcentual' })).toHaveValue(0)
  await usuario.click(screen.getByRole('button', { name: 'Agregar Bujía NGK al carrito' }))
  await usuario.click(screen.getByRole('button', { name: 'Sumar Bujía NGK' }))

  expect(screen.getByText('2 artículos')).toBeInTheDocument()
  expect(screen.getByText('$20.168')).toBeInTheDocument()
  expect(screen.getByText('$3.832')).toBeInTheDocument()
  expect(screen.getByText('$0')).toBeInTheDocument()
  expect(screen.getByText('$24.000')).toBeInTheDocument()
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

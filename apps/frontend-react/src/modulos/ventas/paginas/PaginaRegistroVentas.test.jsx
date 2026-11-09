import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { confirmarEntregaVenta, listarVentas, obtenerDetalleVenta } from '../api/apiVentas'
import { imprimirComprobanteVenta } from '@/utilidades/imprimirComprobanteVenta'

import PaginaRegistroVentas from './PaginaRegistroVentas'

vi.mock('../api/apiVentas', () => ({
  anularVenta: vi.fn(),
  confirmarEntregaVenta: vi.fn(),
  listarVentas: vi.fn(),
  obtenerDetalleVenta: vi.fn(),
}))
vi.mock('@/utilidades/imprimirComprobanteVenta', () => ({
  imprimirComprobanteVenta: vi.fn(),
}))

const VENTA = {
  id: 45,
  numero_venta: 'V-00045',
  cliente_nombre: 'Carlos Ramírez',
  fecha_venta: '2026-11-08T10:00:00Z',
  tipo_pago: 'contado',
  estado: 'pagada',
  estado_pago: 'PAGADA',
  estado_entrega: 'pendiente_entrega',
  cantidad_items: 1,
  total: '25000.00',
}

beforeEach(() => {
  vi.clearAllMocks()
  listarVentas.mockResolvedValue([VENTA])
  confirmarEntregaVenta.mockResolvedValue({})
  obtenerDetalleVenta.mockResolvedValue({ ...VENTA, detalles: [] })
})

afterEach(() => {
  vi.restoreAllMocks()
})

test('descarga el comprobante PDF de una venta registrada', async () => {
  const usuario = userEvent.setup()
  const ventana = { close: vi.fn() }
  const detalle = { ...VENTA, detalles: [] }
  vi.spyOn(window, 'open').mockReturnValue(ventana)
  obtenerDetalleVenta.mockResolvedValue(detalle)
  renderizarEnRuta(<PaginaRegistroVentas />, '/ventas')

  await usuario.click(
    await screen.findByRole('button', { name: 'Descargar PDF de la venta V-00045' })
  )

  await waitFor(() => {
    expect(obtenerDetalleVenta).toHaveBeenCalledWith(45)
    expect(imprimirComprobanteVenta).toHaveBeenCalledWith(detalle, ventana)
  })
})

test('pide confirmar la entrega y permite cancelarla antes de actualizarla', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaRegistroVentas />, '/ventas')

  expect(screen.queryByRole('button', { name: 'Marcar entregada' })).not.toBeInTheDocument()
  await usuario.click(await screen.findByRole('button', { name: 'Ver detalle' }))
  await usuario.click(await screen.findByRole('button', { name: 'Marcar entregada' }))
  expect(screen.getByRole('alertdialog')).toHaveTextContent(
    'V-00045 ya fue entregada a Carlos Ramírez'
  )

  await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(confirmarEntregaVenta).not.toHaveBeenCalled()

  await usuario.click(screen.getByRole('button', { name: 'Marcar entregada' }))
  await usuario.click(screen.getByRole('button', { name: 'Confirmar entrega' }))

  await waitFor(() => expect(confirmarEntregaVenta).toHaveBeenCalledWith(45))
  await waitFor(() => expect(listarVentas).toHaveBeenCalledTimes(2))
})

test('muestra el estado parcial de pago en el registro de ventas', async () => {
  listarVentas.mockResolvedValue([{ ...VENTA, tipo_pago: 'credito', estado_pago: 'PARCIAL' }])
  renderizarEnRuta(<PaginaRegistroVentas />, '/ventas')

  expect(await screen.findByText('PARCIAL')).toBeInTheDocument()
})

test('oculta la acción de anular cuando la venta ya tiene pagos', async () => {
  const usuario = userEvent.setup()
  listarVentas.mockResolvedValue([{ ...VENTA, tipo_pago: 'credito', estado_pago: 'PARCIAL' }])
  obtenerDetalleVenta.mockResolvedValue({
    ...VENTA,
    tipo_pago: 'credito',
    estado_pago: 'PARCIAL',
    puede_anular: false,
    detalles: [],
  })
  renderizarEnRuta(<PaginaRegistroVentas />, '/ventas')

  await usuario.click(await screen.findByRole('button', { name: 'Ver detalle' }))

  expect(screen.getAllByText('PARCIAL')).toHaveLength(2)
  expect(screen.queryByRole('button', { name: 'Anular venta' })).not.toBeInTheDocument()
})

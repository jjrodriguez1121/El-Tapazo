import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { confirmarEntregaVenta, listarVentas } from '../api/apiVentas'

import PaginaRegistroVentas from './PaginaRegistroVentas'

vi.mock('../api/apiVentas', () => ({
  anularVenta: vi.fn(),
  confirmarEntregaVenta: vi.fn(),
  listarVentas: vi.fn(),
  obtenerDetalleVenta: vi.fn(),
}))

const VENTA = {
  id: 45,
  numero_venta: 'V-00045',
  cliente_nombre: 'Carlos Ramírez',
  fecha_venta: '2026-11-08T10:00:00Z',
  tipo_pago: 'contado',
  estado: 'pagada',
  estado_entrega: 'pendiente_entrega',
  cantidad_items: 1,
  total: '25000.00',
}

beforeEach(() => {
  vi.clearAllMocks()
  listarVentas.mockResolvedValue([VENTA])
  confirmarEntregaVenta.mockResolvedValue({})
})

test('pide confirmar la entrega y permite cancelarla antes de actualizarla', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaRegistroVentas />, '/ventas')

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

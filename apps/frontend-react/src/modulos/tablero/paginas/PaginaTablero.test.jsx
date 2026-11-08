import { screen, within } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaTablero from './PaginaTablero'

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: { get: vi.fn(() => Promise.resolve({ data: [] })) },
}))

test('exige un rango de fechas para consultar el dashboard', async () => {
  renderizarEnRuta(<PaginaTablero />, '/inicio')

  expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
  expect(screen.getByLabelText('Desde')).toBeRequired()
  expect(screen.getByLabelText('Hasta')).toBeRequired()
  expect(await screen.findByRole('button', { name: 'Aplicar filtro' })).toBeInTheDocument()
  expect(screen.getByText('Ventas facturadas')).toBeInTheDocument()
})

test('las alertas de stock llevan al inventario', () => {
  renderizarEnRuta(<PaginaTablero />, '/inicio')

  const alertas = screen.getByRole('heading', { name: 'Alertas de stock' }).closest('section')
  expect(within(alertas).getByRole('link', { name: 'Ver inventario' })).toHaveAttribute(
    'href',
    '/productos'
  )
})

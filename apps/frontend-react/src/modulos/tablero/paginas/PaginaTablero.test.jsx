import { screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaTablero from './PaginaTablero'

test('enseña las cuatro cifras del día con su formato', () => {
  renderizarEnRuta(<PaginaTablero />, '/inicio')

  expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
  expect(screen.getByText('Ventas de hoy')).toBeInTheDocument()
  expect(screen.getByText('$1.240.000')).toBeInTheDocument()
  expect(screen.getByText('Stock bajo')).toBeInTheDocument()
})

test('las alertas de stock cuentan cuántos productos están bajos y llevan al inventario', () => {
  renderizarEnRuta(<PaginaTablero />, '/inicio')

  const alertas = screen.getByRole('heading', { name: 'Alertas de stock' }).closest('section')
  expect(within(alertas).getByText('5 bajos')).toBeInTheDocument()
  expect(within(alertas).getByRole('link', { name: 'Ver inventario' })).toHaveAttribute(
    'href',
    '/productos'
  )
})

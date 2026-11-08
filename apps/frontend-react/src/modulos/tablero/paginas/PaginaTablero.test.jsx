import { screen, within } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import { clienteApi } from '@/librerias/clienteApi'
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

test('carga las alertas de stock de todas las páginas', async () => {
  clienteApi.get.mockReset()
  clienteApi.get.mockImplementation((ruta, configuracion) => {
    if (ruta === '/inventario/existencias/bajo-minimo/') {
      if (configuracion.params.page === 1) {
        return Promise.resolve({
          data: {
            count: 21,
            next: '?page=2',
            results: Array.from({ length: 20 }, (_, indice) => ({
              id: indice + 1,
              producto: { nombre: `Producto ${indice + 1}` },
              cantidad_disponible: indice === 0 ? '0.00' : '2.00',
            })),
          },
        })
      }

      return Promise.resolve({
        data: {
          count: 21,
          next: null,
          results: [
            {
              id: 21,
              producto: { nombre: 'Producto agotado 21' },
              cantidad_disponible: '0.00',
            },
          ],
        },
      })
    }

    return Promise.resolve({ data: [] })
  })

  renderizarEnRuta(<PaginaTablero />, '/inicio')

  const alertas = screen.getByRole('heading', { name: 'Alertas de stock' }).closest('section')
  expect(await within(alertas).findByText('Producto agotado 21')).toBeInTheDocument()
  expect(within(alertas).getByText('21 bajos')).toBeInTheDocument()
  expect(within(alertas).getAllByText('0 und')).toHaveLength(2)
})

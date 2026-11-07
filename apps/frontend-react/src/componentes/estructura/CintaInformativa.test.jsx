import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import CintaInformativa from './CintaInformativa'

const MENSAJES_PRUEBA = [
  {
    id: 'test-1',
    categoria: 'Energía',
    icono: () => <span data-testid="icono-1">💡</span>,
    colorIcono: 'text-alerta-700',
    colorFondoIcono: 'bg-alerta-50',
    texto: 'Mantén apagadas las luces que no necesites.',
  },
  {
    id: 'test-2',
    categoria: 'Envases',
    icono: () => <span data-testid="icono-2">📦</span>,
    colorIcono: 'text-azul-600',
    colorFondoIcono: 'bg-azul-50',
    texto: 'Almacena los envases retornables en un lugar seguro y en sus canastillas.',
  },
]

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

test('muestra el primer mensaje y su categoría al renderizar', () => {
  render(<CintaInformativa mensajes={MENSAJES_PRUEBA} />)

  expect(screen.getByText('Energía')).toBeInTheDocument()
  expect(
    screen.getByText('Mantén apagadas las luces que no necesites.')
  ).toBeInTheDocument()
  expect(screen.getByText('1/2')).toBeInTheDocument()
})

test('permite avanzar y retroceder manualmente entre mensajes', async () => {
  render(<CintaInformativa mensajes={MENSAJES_PRUEBA} />)

  // Avanzar al segundo mensaje
  fireEvent.click(screen.getByRole('button', { name: 'Siguiente mensaje' }))
  expect(screen.getByText('Envases')).toBeInTheDocument()
  expect(
    screen.getByText('Almacena los envases retornables en un lugar seguro y en sus canastillas.')
  ).toBeInTheDocument()
  expect(screen.getByText('2/2')).toBeInTheDocument()

  // Retroceder de nuevo al primero
  fireEvent.click(screen.getByRole('button', { name: 'Mensaje anterior' }))
  expect(screen.getByText('Energía')).toBeInTheDocument()
  expect(screen.getByText('1/2')).toBeInTheDocument()
})

test('rota automáticamente cada intervalo establecido', () => {
  render(<CintaInformativa mensajes={MENSAJES_PRUEBA} intervaloMs={5000} />)

  expect(screen.getByText('1/2')).toBeInTheDocument()

  act(() => {
    vi.advanceTimersByTime(5000)
  })

  expect(screen.getByText('2/2')).toBeInTheDocument()
  expect(screen.getByText('Envases')).toBeInTheDocument()

  act(() => {
    vi.advanceTimersByTime(5000)
  })

  // Regresa al primer mensaje por rotación cíclica
  expect(screen.getByText('1/2')).toBeInTheDocument()
  expect(screen.getByText('Energía')).toBeInTheDocument()
})

test('pausa la rotación automática mientras el cursor está encima y reanuda al salir', () => {
  render(<CintaInformativa mensajes={MENSAJES_PRUEBA} intervaloMs={5000} />)

  const contenedor = screen.getByRole('complementary', {
    name: 'Buenas prácticas y gestión ambiental',
  })

  // Poner el mouse encima (hover)
  fireEvent.mouseEnter(contenedor)

  act(() => {
    vi.advanceTimersByTime(5000)
  })

  // Sigue en 1/2 porque está en pausa
  expect(screen.getByText('1/2')).toBeInTheDocument()

  // Retirar el mouse
  fireEvent.mouseLeave(contenedor)

  act(() => {
    vi.advanceTimersByTime(5000)
  })

  // Ahora sí avanza a 2/2
  expect(screen.getByText('2/2')).toBeInTheDocument()
})

import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import RecordatorioDePausa from './RecordatorioDePausa'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

function registrarActividad() {
  fireEvent.pointerDown(window)
}

test('muestra el recordatorio tras el intervalo de actividad y exige una lectura breve', () => {
  render(<RecordatorioDePausa intervaloMs={60000} />)

  registrarActividad()
  act(() => vi.advanceTimersByTime(60000))
  registrarActividad()

  expect(screen.getByRole('dialog', { name: 'Es momento de una pausa activa' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Continuar en 5 s' })).toBeDisabled()

  act(() => vi.advanceTimersByTime(5000))

  expect(screen.getByRole('button', { name: 'Tomar mi pausa' })).toBeEnabled()
})

test('aplazar la pausa programa el siguiente aviso con el tiempo indicado', () => {
  render(<RecordatorioDePausa intervaloMs={60000} aplazamientoMs={10000} />)

  registrarActividad()
  act(() => vi.advanceTimersByTime(60000))
  registrarActividad()
  fireEvent.click(screen.getByRole('button', { name: 'Recordar en 10 min' }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

  // Sigue usando la aplicación mientras espera el nuevo aviso.
  act(() => vi.advanceTimersByTime(9000))
  registrarActividad()
  act(() => vi.advanceTimersByTime(1000))
  registrarActividad()

  expect(screen.getByRole('dialog')).toBeInTheDocument()
})

test('espera si la persona está escribiendo en un campo', () => {
  render(
    <>
      <input aria-label="Asunto" />
      <RecordatorioDePausa intervaloMs={60000} />
    </>
  )

  registrarActividad()
  act(() => vi.advanceTimersByTime(60000))
  fireEvent.focus(screen.getByRole('textbox', { name: 'Asunto' }))
  registrarActividad()

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})

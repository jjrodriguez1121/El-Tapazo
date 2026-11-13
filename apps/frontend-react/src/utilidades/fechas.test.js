import { describe, expect, test } from 'vitest'

import { estaEnRangoDeFechas, obtenerFechaLocalIso } from './fechas'

describe('estaEnRangoDeFechas', () => {
  test('incluye ambos extremos del rango', () => {
    expect(estaEnRangoDeFechas('2026-11-08', '2026-11-08', '2026-11-08')).toBe(true)
  })

  test('excluye las fechas que quedan fuera del rango', () => {
    expect(estaEnRangoDeFechas('2026-11-07', '2026-11-08', '2026-11-09')).toBe(false)
    expect(estaEnRangoDeFechas('2026-11-10', '2026-11-08', '2026-11-09')).toBe(false)
  })

  test('permite filtrar con un solo límite y descarta fechas inválidas', () => {
    expect(estaEnRangoDeFechas('2026-11-08', '2026-11-08', '')).toBe(true)
    expect(estaEnRangoDeFechas('', '', '')).toBe(false)
  })

  test('interpreta timestamps y rangos usando la fecha de Bogotá', () => {
    const timestamp = '2026-11-09T04:30:00Z'

    expect(obtenerFechaLocalIso(timestamp)).toBe('2026-11-08')
    expect(estaEnRangoDeFechas(timestamp, '2026-11-08', '2026-11-08')).toBe(true)
  })
})

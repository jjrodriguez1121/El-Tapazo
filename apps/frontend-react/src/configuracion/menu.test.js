import { expect, test } from 'vitest'

import { seccionesVisibles } from './menu'

const etiquetasDe = (secciones) =>
  secciones.flatMap((seccion) => seccion.elementos.map((elemento) => elemento.etiqueta))

test('el administrador ve todas las secciones', () => {
  const etiquetas = etiquetasDe(seccionesVisibles(true))

  expect(etiquetas).toContain('Productos')
  expect(etiquetas).toContain('Pedidos')
  expect(etiquetas).toContain('Pulseras')
})

test('mesero y cajero no ven lo que es del administrador', () => {
  const etiquetas = etiquetasDe(seccionesVisibles(false))

  expect(etiquetas).toEqual([
    'Dashboard',
    'Punto de venta',
    'Jornadas y caja',
    'Cuentas',
    'Clientes',
    'PQRs',
  ])
})

test('una sección que se queda sin elementos no aparece', () => {
  const titulos = seccionesVisibles(false).map((seccion) => seccion.titulo)

  expect(titulos).not.toContain('Inventario')
  expect(titulos).not.toContain('Distribución')
})

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaPqrs from './PaginaPqrs'

test('renderiza el título de PQRs y el formulario de radicación', () => {
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  expect(screen.getByRole('heading', { name: 'PQRs' })).toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: 'Radicar nueva PQR de cliente' })
  ).toBeInTheDocument()
  expect(screen.getByText('Por Servicio 🚚')).toBeInTheDocument()
  expect(screen.getByText('Por Productos 📦')).toBeInTheDocument()
})

test('muestra las PQRs de ejemplo de la distribuidora con clasificación de Servicio y Productos', () => {
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  expect(screen.getByText(/Minimercado La 70/i)).toBeInTheDocument()
  expect(screen.getByText('Botellas quebradas en canastilla de Águila Light')).toBeInTheDocument()
  expect(screen.getByText('Retraso en la entrega de la ruta de los jueves')).toBeInTheDocument()
})

test('permite radicar una PQR de cliente por motivo de Servicio con canal telefónico o presencial', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  // Llenar datos del cliente solicitante de la distribuidora
  await usuario.type(
    screen.getByLabelText(/Nombre completo o Razón social/i),
    'Estanco Central Bello'
  )
  await usuario.type(
    screen.getByLabelText(/NIT \/ Documento/i),
    '901234567-8'
  )
  await usuario.type(
    screen.getByLabelText(/Teléfono \/ Celular/i),
    '3109876543'
  )

  // Seleccionar canal de recepción (telefónico o presencial)
  await usuario.selectOptions(
    screen.getByLabelText(/Canal de recepción/i),
    'presencial'
  )

  // Seleccionar motivo: Servicio
  await usuario.click(screen.getByRole('radio', { name: /Servicio/i }))

  // Seleccionar tipo de PQR
  await usuario.click(screen.getByRole('button', { name: 'Reclamo' }))

  // Llenar asunto y descripción
  await usuario.type(
    screen.getByLabelText(/Asunto \/ Resumen/i),
    'Inconsistencia en factura respecto a remisión de entrega'
  )
  await usuario.type(
    screen.getByLabelText(/Descripción detallada de la solicitud/i),
    'El cliente reporta que en la factura electrónica se cobraron 10 cajas de cerveza pero solo se entregaron 8 según la remisión física firmada por el conductor.'
  )

  // Enviar formulario
  await usuario.click(screen.getByRole('button', { name: /Radicar PQR/i }))

  // Verificar mensaje de éxito y aparición en la lista
  expect(
    await screen.findByText(/¡La PQR ha sido radicada correctamente/i)
  ).toBeInTheDocument()
  expect(screen.getByText(/Estanco Central Bello/i)).toBeInTheDocument()
  expect(
    screen.getByText('Inconsistencia en factura respecto a remisión de entrega')
  ).toBeInTheDocument()
})

test('permite filtrar el historial de PQRs por ámbito de Servicio y Productos', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  // Filtrar solo por Productos
  await usuario.click(screen.getByRole('button', { name: '📦 Productos' }))
  expect(
    screen.getByText('Botellas quebradas en canastilla de Águila Light')
  ).toBeInTheDocument()
  expect(
    screen.queryByText('Retraso en la entrega de la ruta de los jueves')
  ).not.toBeInTheDocument()

  // Filtrar solo por Servicio
  await usuario.click(screen.getByRole('button', { name: '🚚 Servicio' }))
  expect(
    screen.getByText('Retraso en la entrega de la ruta de los jueves')
  ).toBeInTheDocument()
  expect(
    screen.queryByText('Botellas quebradas en canastilla de Águila Light')
  ).not.toBeInTheDocument()
})

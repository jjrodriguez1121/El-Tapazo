import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import { crearPqr, listarPqrs, obtenerResumenPqrs, registrarSeguimientoPqr } from '../api/apiPqrs'

import PaginaPqrs from './PaginaPqrs'

vi.mock('../api/apiPqrs', () => ({
  crearPqr: vi.fn(),
  listarPqrs: vi.fn(),
  obtenerResumenPqrs: vi.fn(),
  registrarSeguimientoPqr: vi.fn(),
}))

const pqrEjemplo = {
  id: 8,
  radicado: 'PQR-000008',
  nombre_solicitante: 'Estanco Central Bello',
  documento_solicitante: '901234567-8',
  telefono_solicitante: '3109876543',
  tipo: 'reclamo',
  ambito: 'servicio',
  canal: 'presencial',
  asunto: 'Inconsistencia en factura de entrega',
  descripcion: 'Se entregaron menos unidades que las facturadas.',
  estado: 'radicada',
  fecha_radicacion: '2026-10-12T16:40:00Z',
  responsable_nombre: '',
  seguimientos: [],
}

const paginaVacia = { count: 0, results: [], previous: null, next: null }

beforeEach(() => {
  listarPqrs.mockReset().mockResolvedValue(paginaVacia)
  crearPqr.mockReset()
  obtenerResumenPqrs.mockReset().mockResolvedValue({
    total: 0,
    servicio: 0,
    productos: 0,
    pendientes: 0,
  })
  registrarSeguimientoPqr.mockReset()
})

afterEach(() => vi.restoreAllMocks())

test('carga el historial persistido y los indicadores de PQR', async () => {
  listarPqrs.mockResolvedValue({
    count: 1,
    results: [pqrEjemplo],
    previous: null,
    next: null,
  })
  obtenerResumenPqrs.mockResolvedValue({
    total: 1,
    servicio: 1,
    productos: 0,
    pendientes: 1,
  })
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  expect(await screen.findByText('Inconsistencia en factura de entrega')).toBeInTheDocument()
  expect(screen.getByText('PQR-000008')).toBeInTheDocument()
  expect(screen.getByText('Pendientes').nextElementSibling).toHaveTextContent('1')
  expect(listarPqrs).toHaveBeenCalledWith({
    page: 1,
    ambito: '',
    search: '',
    respuesta: '',
  })
})

test('filtra PQRs que tienen respuesta registrada', async () => {
  const usuario = userEvent.setup()
  listarPqrs.mockResolvedValue(paginaVacia)
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  await usuario.selectOptions(screen.getByLabelText('Filtrar por respuesta'), 'si')

  await waitFor(() =>
    expect(listarPqrs).toHaveBeenLastCalledWith({
      page: 1,
      ambito: '',
      search: '',
      respuesta: 'si',
    })
  )
})

test('filtra PQRs que aún no tienen respuesta', async () => {
  const usuario = userEvent.setup()
  listarPqrs.mockResolvedValue(paginaVacia)
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  await usuario.selectOptions(screen.getByLabelText('Filtrar por respuesta'), 'no')

  await waitFor(() =>
    expect(listarPqrs).toHaveBeenLastCalledWith({
      page: 1,
      ambito: '',
      search: '',
      respuesta: 'no',
    })
  )
})

test('radica la PQR con la API y muestra el radicado persistente', async () => {
  const usuario = userEvent.setup()
  listarPqrs.mockResolvedValueOnce(paginaVacia).mockResolvedValue({
    count: 1,
    results: [pqrEjemplo],
    previous: null,
    next: null,
  })
  crearPqr.mockResolvedValue(pqrEjemplo)
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  await usuario.type(
    screen.getByLabelText(/Nombre completo o Razón social/i),
    'Estanco Central Bello'
  )
  await usuario.type(screen.getByLabelText(/NIT \/ Documento/i), '901234567-8')
  await usuario.selectOptions(screen.getByLabelText(/Canal de recepción/i), 'presencial')
  await usuario.click(screen.getByRole('radio', { name: /Servicio/i }))
  await usuario.click(screen.getByRole('button', { name: 'Reclamo' }))
  await usuario.type(
    screen.getByLabelText(/Asunto \/ Resumen/i),
    'Inconsistencia en factura de entrega'
  )
  await usuario.type(
    screen.getByLabelText(/Descripción detallada de la solicitud/i),
    'Se entregaron menos unidades que las facturadas.'
  )
  await usuario.click(screen.getByRole('button', { name: /Radicar PQR/i }))

  expect(await screen.findByText(/Número de radicado: PQR-000008/i)).toBeInTheDocument()
  expect(crearPqr).toHaveBeenCalledWith(
    expect.objectContaining({
      nombre_solicitante: 'Estanco Central Bello',
      documento_solicitante: '901234567-8',
      tipo: 'reclamo',
      ambito: 'servicio',
      canal: 'presencial',
    })
  )
  expect(await screen.findByText('PQR-000008')).toBeInTheDocument()
})

test('muestra errores útiles y no envía una PQR con nombre sin contenido', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  await usuario.type(screen.getByLabelText(/Nombre completo o Razón social/i), '   ')
  await usuario.type(screen.getByLabelText(/Asunto \/ Resumen/i), 'Factura')
  await usuario.type(
    screen.getByLabelText(/Descripción detallada de la solicitud/i),
    'Descripción válida de la solicitud'
  )
  await usuario.click(screen.getByRole('button', { name: /Radicar PQR/i }))

  expect(await screen.findByText('Escribe al menos 3 caracteres.')).toBeInTheDocument()
  expect(crearPqr).not.toHaveBeenCalled()
})

test('registra una respuesta en el historial y refresca el estado', async () => {
  const usuario = userEvent.setup()
  const pqrConHistorial = {
    ...pqrEjemplo,
    estado: 'respondida',
    seguimientos: [
      {
        id: 12,
        tipo: 'respuesta',
        contenido: 'Se realizará el ajuste en el próximo despacho.',
        estado_anterior: 'radicada',
        estado_nuevo: 'respondida',
        usuario_nombre: 'Ana Ríos',
        visible_solicitante: true,
        creado_en: '2026-10-13T10:00:00Z',
      },
    ],
  }
  listarPqrs.mockResolvedValue({
    count: 1,
    results: [pqrConHistorial],
    previous: null,
    next: null,
  })
  registrarSeguimientoPqr.mockResolvedValue(pqrConHistorial)
  renderizarEnRuta(<PaginaPqrs />, '/pqrs')

  await screen.findByText('Inconsistencia en factura de entrega')
  await usuario.selectOptions(screen.getByLabelText('Registrar gestión'), 'respuesta')
  await usuario.type(
    screen.getByLabelText('Respuesta al solicitante'),
    'Se realizará el ajuste en el próximo despacho.'
  )
  await usuario.click(screen.getByRole('button', { name: 'Guardar gestión' }))

  await waitFor(() =>
    expect(registrarSeguimientoPqr).toHaveBeenCalledWith(8, {
      tipo: 'respuesta',
      contenido: 'Se realizará el ajuste en el próximo despacho.',
    })
  )
  expect(
    await screen.findByText('Se realizará el ajuste en el próximo despacho.')
  ).toBeInTheDocument()
  expect(screen.getByText('Respondida')).toBeInTheDocument()
})

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderizarEnRuta } from '@/pruebas/renderizar'

import PaginaClientes from './PaginaClientes'

vi.mock('@/librerias/clienteApi', () => ({
  clienteApi: {
    get: vi.fn(async () => ({
      data: [
        {
          id: 1,
          nombre_completo: 'Carlos Ramírez',
          nombre: 'Carlos',
          apellido: 'Ramírez',
          tipo_documento: 'cedula',
          numero_documento: '1045300123',
          fecha_nacimiento: '1992-04-18',
          telefono: '3005551234',
          correo: 'carlos@example.com',
        },
        {
          id: 2,
          nombre_completo: 'Andrés Patiño',
          nombre: 'Andrés',
          apellido: 'Patiño',
          tipo_documento: 'cedula',
          numero_documento: '1018774290',
          fecha_nacimiento: '1996-01-27',
          telefono: '3016789012',
          correo: '',
        },
      ],
    })),
    post: vi.fn(async (_ruta, datos) => ({
      data: {
        id: 3,
        nombre_completo: `${datos.nombre} ${datos.apellido}`,
        ...datos,
        numero_documento: datos.numero_documento,
        tipo_documento: datos.tipo_documento,
      },
    })),
  },
}))

test('muestra los clientes cargados desde el backend', async () => {
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  expect(screen.getByRole('heading', { name: 'Clientes' })).toBeInTheDocument()
  expect(await screen.findByText('Carlos Ramírez')).toBeInTheDocument()
  expect(screen.getByText('Andrés Patiño')).toBeInTheDocument()
})

test('agrega una persona al listado local', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  await usuario.click(screen.getByRole('button', { name: 'Nuevo cliente' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre completo' }), 'Lucía Torres')
  await usuario.type(screen.getByRole('textbox', { name: 'Teléfono' }), '3001234567')
  await usuario.type(screen.getByRole('textbox', { name: 'Número de documento' }), '1045998877')
  await usuario.type(screen.getByLabelText('Fecha de nacimiento'), '1995-03-21')
  await usuario.click(screen.getByRole('button', { name: 'Guardar cliente' }))

  expect(await screen.findByText('Lucía Torres')).toBeInTheDocument()
  expect(screen.getAllByText('Al día')).toHaveLength(3)
})

test('cambia el formulario a establecimiento y muestra contacto', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  await usuario.click(screen.getByRole('button', { name: 'Nuevo cliente' }))
  await usuario.click(screen.getByRole('radio', { name: 'Establecimiento' }))

  expect(screen.getByRole('textbox', { name: 'Nombre del establecimiento' })).toBeInTheDocument()
  expect(screen.getByRole('textbox', { name: 'NIT' })).toBeInTheDocument()
  expect(screen.getByRole('textbox', { name: 'Persona de contacto' })).toBeInTheDocument()
  expect(screen.getByLabelText('Tipo de establecimiento')).toBeInTheDocument()
})

test('rechaza un documento duplicado y un correo inválido', async () => {
  const usuario = userEvent.setup()
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  await usuario.click(screen.getByRole('button', { name: 'Nuevo cliente' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Nombre completo' }), 'Carlos Repetido')
  await usuario.type(screen.getByRole('textbox', { name: 'Teléfono' }), '3001234567')
  await usuario.type(screen.getByRole('textbox', { name: 'Número de documento' }), '1045300123')
  await usuario.type(screen.getByLabelText('Fecha de nacimiento'), '1995-03-21')
  await usuario.click(screen.getByRole('button', { name: 'Guardar cliente' }))

  expect(screen.getByText('Ya existe un cliente con ese documento o NIT.')).toBeInTheDocument()

  await usuario.clear(screen.getByRole('textbox', { name: 'Número de documento' }))
  await usuario.type(screen.getByRole('textbox', { name: 'Número de documento' }), '1045998877')
  await usuario.type(screen.getByRole('textbox', { name: 'Correo electrónico' }), 'correo-mal')
  await usuario.click(screen.getByRole('button', { name: 'Guardar cliente' }))

  expect(screen.getByText('Ese correo no parece válido.')).toBeInTheDocument()
})
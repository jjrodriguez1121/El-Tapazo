import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import { borrarSesion, guardarSesion } from '@/estado/sesion'
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
          saldo_pendiente: '27500.00',
          activo: true,
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
          activo: true,
        },
      ],
    })),
    post: vi.fn(async (ruta, datos) => {
      if (ruta.includes('/desactivacion/')) {
        return { data: { id: Number(ruta.match(/(\d+)/)?.[1]), activo: false } }
      }
      if (ruta.includes('/activacion/')) {
        return { data: { id: Number(ruta.match(/(\d+)/)?.[1]), activo: true } }
      }
      return {
        data: {
          id: 3,
          nombre_completo: `${datos.nombre} ${datos.apellido}`,
          ...datos,
          numero_documento: datos.numero_documento,
          tipo_documento: datos.tipo_documento,
          activo: true,
        },
      }
    }),
  },
}))

afterEach(() => {
  vi.restoreAllMocks()
  act(() => borrarSesion())
})

function iniciarComoAdmin() {
  guardarSesion({
    tokenDeAcceso: 'acceso',
    tokenDeRefresco: 'refresco',
    usuario: { id: 1, rol: 'admin', esAdministrador: true },
  })
}

test('muestra los clientes cargados desde el backend', async () => {
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  expect(screen.getByRole('heading', { name: 'Clientes' })).toBeInTheDocument()
  expect(await screen.findByText('Carlos Ramírez')).toBeInTheDocument()
  expect(screen.getByText('Andrés Patiño')).toBeInTheDocument()
  expect(screen.getByText('$27.500')).toBeInTheDocument()
  expect(screen.getAllByText('Al día')).toHaveLength(1)
  expect(
    screen.queryByRole('button', { name: 'Desactivar cliente Carlos Ramírez' })
  ).not.toBeInTheDocument()
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

test('desactiva y reactiva un cliente sin eliminar su ficha', async () => {
  const usuario = userEvent.setup()
  iniciarComoAdmin()
  renderizarEnRuta(<PaginaClientes />, '/clientes')

  await usuario.click(
    await screen.findByRole('button', { name: 'Desactivar cliente Carlos Ramírez' })
  )
  expect(screen.getByRole('alertdialog')).toHaveTextContent(
    'Sus ventas y cuentas históricas se conservarán'
  )
  await usuario.click(screen.getByRole('button', { name: 'Desactivar cliente' }))
  await usuario.selectOptions(
    screen.getByRole('combobox', { name: 'Estado de los clientes' }),
    'inactivos'
  )
  expect(await screen.findByText('Carlos Ramírez')).toBeInTheDocument()
  expect(screen.getByText('$27.500')).toBeInTheDocument()
  await usuario.click(screen.getByRole('button', { name: 'Activar cliente Carlos Ramírez' }))
  await usuario.click(screen.getByRole('button', { name: 'Activar cliente' }))

  await usuario.selectOptions(
    screen.getByRole('combobox', { name: 'Estado de los clientes' }),
    'activos'
  )
  expect(await screen.findByText('Carlos Ramírez')).toBeInTheDocument()
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

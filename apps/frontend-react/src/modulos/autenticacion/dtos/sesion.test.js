import { expect, test } from 'vitest'

import { cierreHaciaApi, credencialesHaciaApi, sesionDesdeApi } from './sesion'
import { usuarioDesdeApi } from './usuario'

const USUARIO_DE_LA_API = {
  id: 1,
  correo: 'ana@bar.com',
  nombre: 'Ana',
  apellido: 'Ríos',
  nombre_completo: 'Ana Ríos',
  telefono: '3001234567',
  rol: 'admin',
  es_administrador: true,
  negocio: { id: 3, nombre_comercial: 'Bar El Tapaso' },
  correo_verificado_en: '2026-09-04T15:19:18-05:00',
  fecha_alta: '2026-09-04T15:19:18-05:00',
}

test('sesionDesdeApi traduce los tokens y el usuario a los nombres de la aplicación', () => {
  const sesion = sesionDesdeApi({ acceso: 'a', refresco: 'r', usuario: USUARIO_DE_LA_API })

  expect(sesion).toEqual({
    tokenDeAcceso: 'a',
    tokenDeRefresco: 'r',
    usuario: {
      id: 1,
      correo: 'ana@bar.com',
      nombre: 'Ana',
      apellido: 'Ríos',
      nombreCompleto: 'Ana Ríos',
      telefono: '3001234567',
      rol: 'admin',
      esAdministrador: true,
      negocio: { id: 3, nombreComercial: 'Bar El Tapaso' },
      correoVerificadoEn: '2026-09-04T15:19:18-05:00',
      fechaAlta: '2026-09-04T15:19:18-05:00',
    },
  })
})

test('el staff de la plataforma llega sin negocio', () => {
  expect(usuarioDesdeApi({ ...USUARIO_DE_LA_API, negocio: null }).negocio).toBeNull()
})

test('cierreHaciaApi manda el refresco con el nombre que espera la API', () => {
  expect(cierreHaciaApi('refresco-de-prueba')).toEqual({ refresco: 'refresco-de-prueba' })
})

test('credencialesHaciaApi quita los espacios del correo pero no toca la contraseña', () => {
  expect(credencialesHaciaApi({ correo: '  ana@bar.com ', contrasena: ' clave 1 ' })).toEqual({
    correo: 'ana@bar.com',
    contrasena: ' clave 1 ',
  })
})

import { expect, test } from 'vitest'

import { aceptacionHaciaApi, invitacionPendienteDesdeApi } from './invitacion'

test('invitacionPendienteDesdeApi traduce la fecha de vencimiento', () => {
  const invitacion = invitacionPendienteDesdeApi({
    correo: 'luis@bar.com',
    rol: 'mesero',
    negocio: 'Bar El Tapaso',
    expira_en: '2026-09-11T15:19:18-05:00',
  })

  expect(invitacion).toEqual({
    correo: 'luis@bar.com',
    rol: 'mesero',
    negocio: 'Bar El Tapaso',
    expiraEn: '2026-09-11T15:19:18-05:00',
  })
})

test('aceptacionHaciaApi limpia los datos y no manda ni el correo ni el rol', () => {
  const cuerpo = aceptacionHaciaApi({
    token: 'token-de-prueba',
    nombre: ' Luis ',
    apellido: 'Pérez ',
    telefono: '  ',
    contrasena: ' bar123 ',
    correo: 'otro@bar.com',
    rol: 'admin',
  })

  expect(cuerpo).toEqual({
    token: 'token-de-prueba',
    nombre: 'Luis',
    apellido: 'Pérez',
    telefono: '',
    contrasena: ' bar123 ',
  })
})

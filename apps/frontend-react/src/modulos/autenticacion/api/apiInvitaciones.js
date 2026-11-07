import { clienteApi } from '@/librerias/clienteApi'

import { aceptacionHaciaApi, invitacionPendienteDesdeApi } from '../dtos/invitacion'
import { sesionDesdeApi } from '../dtos/sesion'

export const obtenerInvitacionPendiente = (token) =>
  clienteApi
    .get('/usuarios/invitaciones/pendiente/', { params: { token } })
    .then((respuesta) => invitacionPendienteDesdeApi(respuesta.data))

/** Crea la cuenta y devuelve la sesión ya abierta: no hace falta volver a entrar. */
export const aceptarInvitacion = (datos) =>
  clienteApi
    .post('/usuarios/invitaciones/aceptacion/', aceptacionHaciaApi(datos))
    .then((respuesta) => sesionDesdeApi(respuesta.data))

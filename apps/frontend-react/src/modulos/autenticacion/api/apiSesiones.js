import { clienteApi } from '@/librerias/clienteApi'

import { cierreHaciaApi, credencialesHaciaApi, sesionDesdeApi } from '../dtos/sesion'
import { usuarioDesdeApi } from '../dtos/usuario'

export const iniciarSesion = (credenciales) =>
  clienteApi
    .post('/usuarios/sesiones/', credencialesHaciaApi(credenciales))
    .then((respuesta) => sesionDesdeApi(respuesta.data))

export const obtenerUsuarioActual = () =>
  clienteApi.get('/usuarios/yo/').then((respuesta) => usuarioDesdeApi(respuesta.data))

/** Anula el refresco en el servidor. Responde 204: no hay nada que devolver. */
export const cerrarSesion = (tokenDeRefresco) =>
  clienteApi
    .post('/usuarios/sesiones/cierre/', cierreHaciaApi(tokenDeRefresco))
    .then(() => undefined)

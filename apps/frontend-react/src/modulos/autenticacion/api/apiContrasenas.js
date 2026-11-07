import { clienteApi } from '@/librerias/clienteApi'

import { correoHaciaApi } from '../dtos/correo'
import { nuevaContrasenaHaciaApi } from '../dtos/enlace'

// Responde 202 exista o no el correo, a propósito: no hay nada que devolver.
export const solicitarRecuperacion = (correo) =>
  clienteApi
    .post('/usuarios/contrasena/recuperacion/', correoHaciaApi(correo))
    .then(() => undefined)

export const restablecerContrasena = (datos) =>
  clienteApi
    .post('/usuarios/contrasena/restablecimiento/', nuevaContrasenaHaciaApi(datos))
    .then(() => undefined)

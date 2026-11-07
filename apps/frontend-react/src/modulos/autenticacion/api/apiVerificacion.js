import { clienteApi } from '@/librerias/clienteApi'

import { correoHaciaApi } from '../dtos/correo'
import { enlaceHaciaApi } from '../dtos/enlace'

// Responde 202 exista o no el correo, por el mismo motivo que la recuperación.
export const solicitarVerificacion = (correo) =>
  clienteApi
    .post('/usuarios/verificacion-correo/solicitud/', correoHaciaApi(correo))
    .then(() => undefined)

export const confirmarVerificacion = (enlace) =>
  clienteApi
    .post('/usuarios/verificacion-correo/confirmacion/', enlaceHaciaApi(enlace))
    .then(() => undefined)

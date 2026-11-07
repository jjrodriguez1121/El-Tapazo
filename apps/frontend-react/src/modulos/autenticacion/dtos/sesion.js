import { usuarioDesdeApi } from './usuario'

/** Lo que manda el formulario de acceso. El correo viaja sin espacios; la contraseña, tal cual. */
export const credencialesHaciaApi = ({ correo, contrasena }) => ({
  correo: correo.trim(),
  contrasena,
})

/** Lo que manda «Salir»: el refresco que el servidor tiene que anular. */
export const cierreHaciaApi = (tokenDeRefresco) => ({ refresco: tokenDeRefresco })

/** Una sesión recién abierta: los dos tokens y quién entró. */
export const sesionDesdeApi = (sesion) => ({
  tokenDeAcceso: sesion.acceso,
  tokenDeRefresco: sesion.refresco,
  usuario: usuarioDesdeApi(sesion.usuario),
})

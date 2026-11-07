/*
 * Los enlaces de recuperación y de verificación traen dos piezas en la URL,
 * `?uid=…&token=…`, que la persona no ve ni escribe.
 */

export const enlaceDesdeParametros = (parametros) => ({
  uid: parametros.get('uid') ?? '',
  token: parametros.get('token') ?? '',
})

export const enlaceEstaCompleto = ({ uid, token }) => Boolean(uid && token)

export const enlaceHaciaApi = ({ uid, token }) => ({ uid, token })

/** Las dos piezas del enlace más la contraseña que eligió la persona. */
export const nuevaContrasenaHaciaApi = ({ uid, token, contrasena }) => ({ uid, token, contrasena })

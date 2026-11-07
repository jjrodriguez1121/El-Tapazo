/*
 * Cómo leer un error de la API. Todos llegan con la misma forma:
 * { "error": { "codigo": "...", "mensaje": "...", "detalles": {} } }
 *
 * Las pantallas deciden con el `codigo`, que es estable, y muestran el
 * `mensaje`, que ya viene escrito para una persona. Nunca al revés.
 */

export const MENSAJE_POR_DEFECTO = 'No se pudo completar la operación. Inténtalo otra vez.'
export const MENSAJE_SIN_CONEXION =
  'No pudimos conectarnos con el servidor. Revisa tu conexión e inténtalo otra vez.'

/** No hubo respuesta: sin red, el servidor apagado o se agotó la espera. */
export const esErrorDeConexion = (error) => error?.isAxiosError === true && !error.response

/** El código estable del error, para reaccionar distinto según el caso. */
export const codigoDeError = (error) => error?.response?.data?.error?.codigo

/** El mensaje listo para mostrarle a una persona. */
export function mensajeDeError(error) {
  if (esErrorDeConexion(error)) return MENSAJE_SIN_CONEXION
  return error?.response?.data?.error?.mensaje ?? MENSAJE_POR_DEFECTO
}

/** Los errores por campo (`{ nombre: ['...'] }`), para pintarlos bajo cada input. */
export const erroresDeCampo = (error) => error?.response?.data?.error?.detalles ?? {}

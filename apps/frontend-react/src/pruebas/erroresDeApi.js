/*
 * Errores con la misma forma que los que devuelve axios, para simular en las
 * pruebas lo que respondería el backend sin levantarlo.
 */

/** Un error de la API con su `codigo`, como lo arma el manejador del backend. */
export function errorDeApi(
  codigo,
  { mensaje = 'Mensaje del backend.', detalles, estado = 400 } = {}
) {
  const error = new Error(mensaje)
  error.isAxiosError = true
  error.response = {
    status: estado,
    data: { error: { codigo, mensaje, ...(detalles && { detalles }) } },
  }
  return error
}

/** Un error sin respuesta: la red se cayó o el servidor no contestó. */
export function errorDeConexion() {
  const error = new Error('Network Error')
  error.isAxiosError = true
  return error
}

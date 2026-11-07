import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { RUTAS } from '@/configuracion/rutas'
import { borrarSesion, leerRefresco } from '@/estado/sesion'

import { cerrarSesion } from '../api/apiSesiones'

/**
 * Cierra la sesión en el servidor y en el navegador.
 *
 * Se avisa al servidor para que anule el refresco: en un bar los dispositivos
 * se comparten, y borrar solo el localStorage dejaría ese token vivo. Aunque la
 * petición falle —sin red, sesión ya vencida—, aquí se borra igual: quien pulsa
 * «Salir» tiene que salir. También se vacía la caché de consultas, para que
 * quien entre después no vea nada de la persona anterior.
 */
export function useCerrarSesion() {
  const navegar = useNavigate()
  const clienteConsultas = useQueryClient()

  return useMutation({
    mutationFn: () => cerrarSesion(leerRefresco()),
    onSettled: () => {
      borrarSesion()
      clienteConsultas.clear()
      navegar(RUTAS.acceso, { replace: true })
    },
  })
}

import { useQuery } from '@tanstack/react-query'

import { guardarUsuario, leerRefresco, useUsuarioDeSesion } from '@/estado/sesion'

import { obtenerUsuarioActual } from '../api/apiSesiones'

/**
 * Quién tiene la sesión abierta.
 *
 * Tras un F5 el usuario se borra de la memoria, pero el refresco sigue en
 * localStorage: entonces se le pregunta al backend con `GET /yo/`, y el
 * interceptor de `clienteApi` consigue un acceso nuevo por el camino.
 */
export function useSesion() {
  const usuario = useUsuarioDeSesion()
  const hayQueRecuperarla = !usuario && Boolean(leerRefresco())

  const recuperacion = useQuery({
    queryKey: ['usuario-actual'],
    queryFn: async () => {
      const recuperado = await obtenerUsuarioActual()
      guardarUsuario(recuperado)
      return recuperado
    },
    enabled: hayQueRecuperarla,
    retry: false,
  })

  return { usuario, cargando: hayQueRecuperarla && recuperacion.isPending }
}

import { useQuery } from '@tanstack/react-query'

import { confirmarVerificacion } from '../api/apiVerificacion'
import { enlaceEstaCompleto } from '../dtos/enlace'

/**
 * Confirma el correo con el enlace en cuanto se abre la pantalla.
 *
 * Es un POST y aun así va con `useQuery`, a propósito: el enlace sirve una sola
 * vez. Con un efecto, el modo estricto de React lo mandaría dos veces al montar
 * y la segunda respondería «enlace inválido» sobre un correo recién verificado.
 * `useQuery` junta las dos llamadas en una, y con `staleTime: Infinity` no la
 * repite al volver a la pestaña.
 */
export function useConfirmarVerificacion(enlace) {
  return useQuery({
    queryKey: ['confirmacion-de-correo', enlace.uid, enlace.token],
    queryFn: () => confirmarVerificacion(enlace).then(() => true),
    enabled: enlaceEstaCompleto(enlace),
    retry: false,
    staleTime: Infinity,
    gcTime: Infinity,
  })
}

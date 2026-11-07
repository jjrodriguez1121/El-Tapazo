import { useQuery } from '@tanstack/react-query'

import { obtenerInvitacionPendiente } from '../api/apiInvitaciones'

/**
 * De qué es la invitación del enlace. Sin token no pregunta, y no reintenta:
 * una invitación que venció no va a dejar de estar vencida al segundo intento.
 */
export function useInvitacionPendiente(token) {
  return useQuery({
    queryKey: ['invitacion-pendiente', token],
    queryFn: () => obtenerInvitacionPendiente(token),
    enabled: Boolean(token),
    retry: false,
  })
}

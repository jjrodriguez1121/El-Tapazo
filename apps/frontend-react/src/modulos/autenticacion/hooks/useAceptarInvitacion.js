import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { RUTAS } from '@/configuracion/rutas'
import { guardarSesion } from '@/estado/sesion'

import { aceptarInvitacion } from '../api/apiInvitaciones'

/** Crea la cuenta desde la invitación. La persona queda dentro: no pasa por el login. */
export function useAceptarInvitacion() {
  const navegar = useNavigate()

  return useMutation({
    mutationFn: aceptarInvitacion,
    onSuccess: (sesion) => {
      guardarSesion(sesion)
      navegar(RUTAS.inicio, { replace: true })
    },
  })
}

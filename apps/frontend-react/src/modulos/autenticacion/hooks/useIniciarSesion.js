import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { RUTAS } from '@/configuracion/rutas'
import { guardarSesion } from '@/estado/sesion'

import { iniciarSesion } from '../api/apiSesiones'

/** Entra al sistema: guarda la sesión y lleva al inicio. */
export function useIniciarSesion() {
  const navegar = useNavigate()

  return useMutation({
    mutationFn: iniciarSesion,
    onSuccess: (sesion) => {
      guardarSesion(sesion)
      navegar(RUTAS.inicio, { replace: true })
    },
  })
}

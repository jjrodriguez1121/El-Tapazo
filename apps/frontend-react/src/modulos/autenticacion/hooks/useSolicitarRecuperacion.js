import { useMutation } from '@tanstack/react-query'

import { solicitarRecuperacion } from '../api/apiContrasenas'

/** Pide el enlace de «olvidé mi contraseña» para un correo. */
export function useSolicitarRecuperacion() {
  return useMutation({ mutationFn: solicitarRecuperacion })
}

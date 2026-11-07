import { useMutation } from '@tanstack/react-query'

import { solicitarVerificacion } from '../api/apiVerificacion'

/** Pide otro enlace de verificación para un correo. */
export function useSolicitarVerificacion() {
  return useMutation({ mutationFn: solicitarVerificacion })
}

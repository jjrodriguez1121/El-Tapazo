import { useMutation } from '@tanstack/react-query'

import { restablecerContrasena } from '../api/apiContrasenas'

/** Guarda la contraseña nueva con las dos piezas del enlace de recuperación. */
export function useRestablecerContrasena() {
  return useMutation({ mutationFn: restablecerContrasena })
}

import { useMutation } from '@tanstack/react-query'

import { crearCategoria } from '../api/apiCategorias'

export function useCrearCategoria() {
  return useMutation({ mutationFn: crearCategoria })
}
import { useMutation } from '@tanstack/react-query'

import { actualizarCategoria, crearCategoria } from '../api/apiCategorias'

export function useCrearCategoria() {
  return useMutation({ mutationFn: crearCategoria })
}

export function useActualizarCategoria() {
  return useMutation({
    mutationFn: ({ id, datos }) => actualizarCategoria(id, datos),
  })
}
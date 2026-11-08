import { useQuery } from '@tanstack/react-query'

import { obtenerCatalogoDeProductos, obtenerTodasLasCategorias } from '../api/apiListaProductos'

export const CLAVE_CATALOGO_PRODUCTOS = ['catalogo', 'productos']
export const CLAVE_TODAS_LAS_CATEGORIAS = ['catalogo', 'categorias', 'todas']

export function useCatalogoDeProductos() {
  return useQuery({
    queryKey: CLAVE_CATALOGO_PRODUCTOS,
    queryFn: obtenerCatalogoDeProductos,
  })
}

export function useTodasLasCategorias() {
  return useQuery({
    queryKey: CLAVE_TODAS_LAS_CATEGORIAS,
    queryFn: obtenerTodasLasCategorias,
  })
}

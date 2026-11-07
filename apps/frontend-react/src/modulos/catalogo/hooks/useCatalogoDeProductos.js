import { useQuery } from '@tanstack/react-query'

import { obtenerCatalogoDeProductos } from '../api/apiListaProductos'

export const CLAVE_CATALOGO_PRODUCTOS = ['catalogo', 'productos']

export function useCatalogoDeProductos() {
  return useQuery({
    queryKey: CLAVE_CATALOGO_PRODUCTOS,
    queryFn: obtenerCatalogoDeProductos,
  })
}
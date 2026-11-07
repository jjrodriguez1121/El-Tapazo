import { clienteApi } from '@/librerias/clienteApi'

export const crearCategoria = (datos) =>
  clienteApi.post('/catalogo/categorias/', datos).then((respuesta) => respuesta.data)

export const actualizarCategoria = (id, datos) =>
  clienteApi.put(`/catalogo/categorias/${id}/`, datos).then((respuesta) => respuesta.data)

export const desactivarCategoria = (id) =>
  clienteApi.post(`/catalogo/categorias/${id}/desactivacion/`).then((respuesta) => respuesta.data)
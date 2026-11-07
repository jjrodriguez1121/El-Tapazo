import { clienteApi } from '@/librerias/clienteApi'

export const crearCategoria = (datos) =>
  clienteApi.post('/catalogo/categorias/', datos).then((respuesta) => respuesta.data)
import { clienteApi } from '@/librerias/clienteApi'

async function listarTodasLasPaginas(ruta) {
  const resultados = []
  let pagina = 1

  while (true) {
    const { data } = await clienteApi.get(ruta, { params: { page: pagina } })
    if (Array.isArray(data)) return data

    resultados.push(...data.results)
    if (!data.next) return resultados
    pagina += 1
  }
}

export async function obtenerCatalogoDeProductos() {
  const [productos, categorias, existencias] = await Promise.all([
    listarTodasLasPaginas('/catalogo/productos/?activo=true'),
    listarTodasLasPaginas('/catalogo/categorias/?activa=true'),
    listarTodasLasPaginas('/inventario/existencias/'),
  ])

  return { productos, categorias, existencias }
}

export const crearProducto = (datos) =>
  clienteApi.post('/catalogo/productos/', datos).then((respuesta) => respuesta.data)
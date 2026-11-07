import { useState } from 'react'
import { MagnifyingGlassIcon, PackageIcon } from '@phosphor-icons/react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import Insignia from '@/componentes/ui/Insignia'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

const ESTADO_STOCK = {
  disponible: { tono: 'exito', etiqueta: 'En stock' },
  bajo: { tono: 'alerta', etiqueta: 'Stock bajo' },
  agotado: { tono: 'error', etiqueta: 'Sin stock' },
}

function estadoDeExistencias(existencias) {
  if (!existencias.length || existencias.every((existencia) => Number(existencia.cantidad_disponible) <= 0)) {
    return 'agotado'
  }
  return existencias.some((existencia) => existencia.esta_bajo_minimo) ? 'bajo' : 'disponible'
}

export default function PaginaProductos() {
  const catalogo = useCatalogoDeProductos()
  const { state: estadoDeNavegacion } = useLocation()
  const [parametros] = useSearchParams()
  const categoriaDeLaUrl = parametros.get('categoria')
  const [categoriaActiva, setCategoriaActiva] = useState(
    categoriaDeLaUrl ? Number(categoriaDeLaUrl) : 'todas'
  )
  const [busqueda, setBusqueda] = useState('')

  if (catalogo.isPending) return <EsqueletoDeProductos />

  if (catalogo.isError) {
    return (
      <section className="flex flex-col gap-4">
        <h1 className="text-titulo font-bold text-azul-950">Productos</h1>
        <Aviso>{mensajeDeError(catalogo.error)}</Aviso>
        <button
          type="button"
          onClick={() => catalogo.refetch()}
          className="self-start rounded-lg border border-azul-200 px-4 py-2 text-sm font-semibold text-azul-700 hover:bg-azul-50"
        >
          Reintentar
        </button>
      </section>
    )
  }

  const { productos: productosDelCatalogo, categorias, existencias } = catalogo.data
  const productosBaseOriginales = productosDelCatalogo
  const productoActualizado = estadoDeNavegacion?.productoActualizado
  const productosBase = productoActualizado
    ? productosBaseOriginales.map((producto) =>
        String(producto.id) === String(productoActualizado.id) ? productoActualizado : producto
      )
    : productosBaseOriginales
  const productos = productosBase
  const categoriasVisibles = categorias
  const existenciasBaseOriginales = existencias
  const existenciasBase = productoActualizado
    ? [
        ...existenciasBaseOriginales.filter(
          (existencia) => String(existencia.producto.id) !== String(productoActualizado.id)
        ),
        ...(productoActualizado.existencias ?? []),
      ]
    : existenciasBaseOriginales
  const existenciasVisibles = existenciasBase
  const existenciasPorProducto = new Map()
  for (const existencia of existenciasVisibles) {
    const productoId = existencia.producto.id
    existenciasPorProducto.set(productoId, [
      ...(existenciasPorProducto.get(productoId) ?? []),
      existencia,
    ])
  }
  const textoBusqueda = busqueda.trim().toLocaleLowerCase('es-CO')
  const productosFiltrados = productos.filter((producto) => {
    const coincideCategoria =
      categoriaActiva === 'todas' ||
      String(producto.categoria.id) === String(categoriaActiva)
    const coincideBusqueda =
      !textoBusqueda ||
      producto.nombre.toLocaleLowerCase('es-CO').includes(textoBusqueda) ||
      producto.sku.toLocaleLowerCase('es-CO').includes(textoBusqueda)
    return coincideCategoria && coincideBusqueda
  })
  const productosBajoMinimo = new Set(
    existenciasVisibles
      .filter((existencia) => existencia.esta_bajo_minimo)
      .map((existencia) => existencia.producto.id)
  )

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold text-azul-950">Productos</h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            {formatearCantidad(productos.length)} {productos.length === 1 ? 'producto' : 'productos'} en catálogo
            {' · '}
            {formatearCantidad(productosBajoMinimo.size)} con stock bajo
          </p>
        </div>
        <span className="rounded-lg bg-azul-50 px-3 py-2 text-xs font-semibold text-azul-600">
          Altas registradas desde Compras
        </span>
      </header>

      <div className="flex flex-col gap-3">
        <div className="flex gap-2 overflow-x-auto pb-1" aria-label="Filtrar por categoría">
          <button
            type="button"
            aria-pressed={categoriaActiva === 'todas'}
            onClick={() => setCategoriaActiva('todas')}
            className={`inline-flex h-9 flex-none items-center gap-2 rounded-lg border px-3.5 text-xs font-bold transition-colors ${categoriaActiva === 'todas' ? 'border-azul-950 bg-azul-950 text-blanco' : 'border-azul-150 bg-blanco text-azul-700 hover:bg-azul-50'}`}
          >
            <PackageIcon size={15} /> Todas
          </button>
          {categoriasVisibles.map((categoria) => (
            <button
              key={categoria.id}
              type="button"
              aria-pressed={categoriaActiva === categoria.id}
              onClick={() => setCategoriaActiva(categoria.id)}
              className={`h-9 flex-none rounded-lg border px-3.5 text-xs font-semibold transition-colors ${categoriaActiva === categoria.id ? 'border-azul-950 bg-azul-950 text-blanco' : 'border-azul-150 bg-blanco text-azul-700 hover:bg-azul-50'}`}
            >
              {categoria.nombre}
            </button>
          ))}
        </div>

        <label className="relative block max-w-md">
          <MagnifyingGlassIcon
            aria-hidden="true"
            size={18}
            className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-azul-400"
          />
          <input
            type="search"
            aria-label="Buscar producto o SKU"
            placeholder="Buscar producto o SKU"
            value={busqueda}
            onChange={(evento) => setBusqueda(evento.target.value)}
            className="h-10 w-full rounded-xl border border-azul-150 bg-blanco pl-10 pr-3.5 text-sm text-azul-950 outline-none placeholder:text-azul-400 focus:border-azul-500 focus:ring-3 focus:ring-azul-500/15"
          />
        </label>
      </div>

      <section aria-label="Listado de productos" className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[790px] border-collapse text-left">
            <thead className="bg-azul-50/70 text-[11px] font-bold uppercase text-azul-500">
              <tr>
                <th scope="col" className="px-4 py-3.5">Producto</th>
                <th scope="col" className="px-4 py-3.5">Categoría</th>
                <th scope="col" className="px-4 py-3.5">Precio</th>
                <th scope="col" className="px-4 py-3.5">Stock</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-azul-100">
              {productosFiltrados.map((producto) => {
                const existenciasDelProducto = existenciasPorProducto.get(producto.id) ?? []
                const cantidad = existenciasDelProducto.reduce(
                  (total, existencia) => total + Number(existencia.cantidad_disponible),
                  0
                )
                const estado = ESTADO_STOCK[estadoDeExistencias(existenciasDelProducto)]
                return (
                  <tr key={producto.id} className="transition-colors hover:bg-azul-50/40">
                    <td className="px-4 py-3.5">
                      <Link
                        to={`/productos/${producto.id}`}
                        state={{ producto }}
                        aria-label={`Ver producto ${producto.nombre}`}
                        className="group flex min-w-52 items-center gap-3 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-azul-600"
                      >
                        {producto.imagen ? (
                          <img src={producto.imagen} alt="" className="size-9 flex-none rounded-lg object-cover" />
                        ) : (
                          <span className="grid size-9 flex-none place-items-center rounded-lg bg-azul-50 text-azul-500">
                            <PackageIcon size={18} />
                          </span>
                        )}
                        <span className="flex min-w-0 flex-col text-left">
                          <span className="truncate text-sm font-bold text-azul-950 group-hover:text-azul-600">
                            {producto.nombre}
                          </span>
                          <span className="mt-0.5 text-[11px] font-medium text-azul-400">{producto.sku}</span>
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-azul-700">{producto.categoria.nombre}</td>
                    <td className="px-4 py-3.5 text-sm font-bold text-exito-800">
                      {formatearPesos(Number(producto.precio_venta ?? producto.precio_evento))}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-col items-start gap-1">
                        <Insignia tono={estado.tono}>{estado.etiqueta}</Insignia>
                        <span className="text-xs text-azul-500">
                          {formatearCantidad(cantidad)} {producto.unidad ?? 'unidades'}
                        </span>
                      </div>
                    </td>
                  </tr>
                )
              })}
              {!productosFiltrados.length && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <p className="text-sm font-semibold text-azul-700">No hay productos para mostrar.</p>
                    <p className="mt-1 text-xs text-azul-400">
                      Ajusta la búsqueda o selecciona otra categoría.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  )
}
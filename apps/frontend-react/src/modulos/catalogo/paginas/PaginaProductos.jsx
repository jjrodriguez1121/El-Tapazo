import { useState } from 'react'
import { MagnifyingGlassIcon, PackageIcon, PlusIcon } from '@phosphor-icons/react'
import { Link, useLocation } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import Insignia from '@/componentes/ui/Insignia'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import ModalNuevoProducto from '../componentes/ModalNuevoProducto'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'
import { CATEGORIAS_DE_EJEMPLO, PRODUCTOS_DE_EJEMPLO } from '../utilidades/datosDeEjemplo'

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
  const [categoriaActiva, setCategoriaActiva] = useState('todas')
  const [busqueda, setBusqueda] = useState('')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [productosLocales, setProductosLocales] = useState([])

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
  const usandoDatosDeEjemplo = productosDelCatalogo.length === 0
  const productosBaseOriginales = usandoDatosDeEjemplo ? PRODUCTOS_DE_EJEMPLO : productosDelCatalogo
  const productoActualizado = estadoDeNavegacion?.productoActualizado
  const productosBase = productoActualizado
    ? productosBaseOriginales.map((producto) =>
        String(producto.id) === String(productoActualizado.id) ? productoActualizado : producto
      )
    : productosBaseOriginales
  const productos = [...productosBase, ...productosLocales]
  const categoriasVisibles = usandoDatosDeEjemplo ? CATEGORIAS_DE_EJEMPLO : categorias
  const existenciasBaseOriginales = usandoDatosDeEjemplo
    ? PRODUCTOS_DE_EJEMPLO.flatMap((producto) => producto.existencias)
    : existencias
  const existenciasBase = productoActualizado
    ? [
        ...existenciasBaseOriginales.filter(
          (existencia) => String(existencia.producto.id) !== String(productoActualizado.id)
        ),
        ...(productoActualizado.existencias ?? []),
      ]
    : existenciasBaseOriginales
  const existenciasVisibles = [
    ...existenciasBase,
    ...productosLocales.flatMap((producto) => producto.existencias),
  ]
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
      categoriaActiva === 'todas' || producto.categoria.id === categoriaActiva
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

  function agregarProductoLocal(datos) {
    const id = `local-${Date.now()}`
    const estaBajoMinimo = datos.stockMinimo > 0 && datos.stockActual <= datos.stockMinimo
    setProductosLocales((actuales) => [
      ...actuales,
      {
        id,
        nombre: datos.nombre,
        sku: datos.sku,
        categoria: datos.categoria,
        unidad: datos.unidad,
        precio_evento: datos.precioVenta,
        imagen: datos.imagen,
        existencias: [
          {
            producto: { id },
            ubicacion: { nombre: datos.ubicacion },
            cantidad_disponible: datos.stockActual,
            cantidad_minima: datos.stockMinimo,
            esta_bajo_minimo: estaBajoMinimo,
          },
        ],
      },
    ])
  }

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
          {usandoDatosDeEjemplo && (
            <p className="mt-1 text-xs font-semibold text-alerta-700">Datos de ejemplo</p>
          )}
        </div>
        <button
          type="button"
          onClick={() => setModalAbierto(true)}
          disabled={!categoriasVisibles.length}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <PlusIcon size={17} weight="bold" />
          Nuevo producto
        </button>
      </header>

      {!categoriasVisibles.length && (
        <Aviso>No hay categorías activas. Crea una categoría antes de agregar productos.</Aviso>
      )}

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
                <th scope="col" className="px-4 py-3.5">Ubicación</th>
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
                const ubicaciones = [...new Set(existenciasDelProducto.map((existencia) => existencia.ubicacion.nombre))]

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
                      {formatearPesos(Number(producto.precio_evento))}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-col items-start gap-1">
                        <Insignia tono={estado.tono}>{estado.etiqueta}</Insignia>
                        <span className="text-xs text-azul-500">
                          {formatearCantidad(cantidad)} {producto.unidad ?? 'unidades'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-azul-600">
                      {ubicaciones.length ? ubicaciones.join(', ') : 'Sin ubicación'}
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

      {modalAbierto && (
        <ModalNuevoProducto
          categorias={categoriasVisibles}
          productosExistentes={productos}
          alCrear={agregarProductoLocal}
          alCerrar={() => setModalAbierto(false)}
        />
      )}
    </div>
  )
}
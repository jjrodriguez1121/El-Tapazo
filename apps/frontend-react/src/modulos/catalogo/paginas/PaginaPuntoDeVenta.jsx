import { useState } from 'react'
import {
  ImageIcon,
  MinusIcon,
  PackageIcon,
  PlusIcon,
  PrinterIcon,
  ShoppingCartSimpleIcon,
  TrashIcon,
} from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'
import { CATEGORIAS_DE_EJEMPLO, PRODUCTOS_DE_EJEMPLO } from '../utilidades/datosDeEjemplo'

const IVA = 0.19

function ImagenProducto({ producto }) {
  return producto.imagen ? (
    <img src={producto.imagen} alt="" className="h-full w-full object-cover" />
  ) : (
    <div
      aria-hidden="true"
      className="grid h-full w-full place-items-center text-azul-300"
      style={{ backgroundImage: 'repeating-linear-gradient(45deg, #f3f5f5 0 7px, #e8ebec 7px 14px)' }}
    >
      <ImageIcon size={24} />
    </div>
  )
}

export default function PaginaPuntoDeVenta() {
  const catalogo = useCatalogoDeProductos()
  const [categoriaActiva, setCategoriaActiva] = useState('todas')
  const [carrito, setCarrito] = useState([])
  const [porcentajeDescuento, setPorcentajeDescuento] = useState('5')
  const [avisoCobro, setAvisoCobro] = useState('')

  if (catalogo.isPending) return <EsqueletoDeProductos />

  if (catalogo.isError) {
    return (
      <section className="flex flex-col gap-4">
        <h1 className="text-titulo font-bold text-azul-950">Punto de venta</h1>
        <Aviso>{mensajeDeError(catalogo.error)}</Aviso>
        <button
          type="button"
          onClick={() => catalogo.refetch()}
          className="self-start rounded-lg border border-azul-200 px-4 py-2 text-sm font-semibold text-azul-600 hover:bg-azul-50"
        >
          Reintentar
        </button>
      </section>
    )
  }

  const { productos: productosApi, categorias: categoriasApi, existencias: existenciasApi } = catalogo.data
  const usandoEjemplos = productosApi.length === 0
  const productos = usandoEjemplos ? PRODUCTOS_DE_EJEMPLO : productosApi
  const categorias = usandoEjemplos ? CATEGORIAS_DE_EJEMPLO : categoriasApi
  const existencias = usandoEjemplos
    ? PRODUCTOS_DE_EJEMPLO.flatMap((producto) => producto.existencias)
    : existenciasApi
  const existenciasPorProducto = new Map()

  for (const existencia of existencias) {
    const idProducto = String(existencia.producto.id)
    existenciasPorProducto.set(idProducto, [
      ...(existenciasPorProducto.get(idProducto) ?? []),
      existencia,
    ])
  }

  const productosVisibles = productos.filter(
    (producto) => categoriaActiva === 'todas' || String(producto.categoria.id) === categoriaActiva
  )
  const cantidadArticulos = carrito.reduce((total, linea) => total + linea.cantidad, 0)
  const subtotal = carrito.reduce(
    (total, linea) => total + Number(linea.producto.precio_evento) * linea.cantidad,
    0
  )
  const descuento = Math.round(subtotal * (Number(porcentajeDescuento || 0) / 100))
  const impuesto = Math.round(subtotal * IVA)
  const total = subtotal + impuesto - descuento

  function agregarAlCarrito(producto) {
    setAvisoCobro('')
    setCarrito((actual) => {
      const lineaExistente = actual.find((linea) => String(linea.producto.id) === String(producto.id))
      if (lineaExistente) {
        return actual.map((linea) =>
          String(linea.producto.id) === String(producto.id)
            ? { ...linea, cantidad: linea.cantidad + 1 }
            : linea
        )
      }
      return [...actual, { producto, cantidad: 1 }]
    })
  }

  function cambiarCantidad(idProducto, delta) {
    setCarrito((actual) =>
      actual
        .map((linea) =>
          String(linea.producto.id) === String(idProducto)
            ? { ...linea, cantidad: linea.cantidad + delta }
            : linea
        )
        .filter((linea) => linea.cantidad > 0)
    )
    setAvisoCobro('')
  }

  function eliminarDelCarrito(idProducto) {
    setCarrito((actual) =>
      actual.filter((linea) => String(linea.producto.id) !== String(idProducto))
    )
    setAvisoCobro('')
  }

  function cobrar() {
    setAvisoCobro('El cobro e impresión se conectarán cuando se integre el flujo de ventas.')
  }

  return (
    <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_272px]">
      <section className="flex min-w-0 flex-col gap-3.5">
        <header>
          <h1 className="text-titulo font-bold text-azul-950">Punto de venta</h1>
          <p className="mt-1 text-xs font-medium text-azul-400">
            Agrega repuestos al carrito para registrar la venta
            {usandoEjemplos && <span className="ml-2 text-alerta-700">Datos de ejemplo</span>}
          </p>
        </header>

        <div className="flex gap-2 overflow-x-auto pb-1" aria-label="Filtrar productos por categoría">
          <button
            type="button"
            aria-pressed={categoriaActiva === 'todas'}
            onClick={() => setCategoriaActiva('todas')}
            className={`inline-flex h-8 flex-none items-center gap-1.5 rounded-lg border px-3 text-[11px] font-semibold ${categoriaActiva === 'todas' ? 'border-azul-950 bg-azul-950 text-blanco' : 'border-azul-150 bg-blanco text-azul-600 hover:bg-azul-50'}`}
          >
            <PackageIcon size={14} /> Todas
          </button>
          {categorias.map((categoria) => (
            <button
              key={categoria.id}
              type="button"
              aria-pressed={categoriaActiva === String(categoria.id)}
              onClick={() => setCategoriaActiva(String(categoria.id))}
              className={`h-8 flex-none rounded-lg border px-3 text-[11px] font-semibold ${categoriaActiva === String(categoria.id) ? 'border-azul-950 bg-azul-950 text-blanco' : 'border-azul-150 bg-blanco text-azul-600 hover:bg-azul-50'}`}
            >
              {categoria.nombre}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 2xl:grid-cols-5">
          {productosVisibles.map((producto) => {
            const stockDelProducto = existenciasPorProducto.get(String(producto.id)) ?? []
            const disponible = stockDelProducto.reduce(
              (totalStock, existencia) => totalStock + Number(existencia.cantidad_disponible),
              0
            )
            const cantidadEnCarrito =
              carrito.find((linea) => String(linea.producto.id) === String(producto.id))?.cantidad ?? 0
            const ubicacion = stockDelProducto.map((existencia) => existencia.ubicacion.nombre).join(', ')

            return (
              <article
                key={producto.id}
                className="flex min-w-0 flex-col overflow-hidden rounded-xl border border-azul-150 bg-blanco p-2 transition-colors hover:border-azul-300"
              >
                <div className="relative aspect-[4/3] overflow-hidden rounded-lg">
                  <ImagenProducto producto={producto} />
                  <span className="absolute left-2 top-2 rounded bg-blanco/90 px-1.5 py-0.5 font-mono text-[9px] text-azul-700">
                    {producto.sku}
                  </span>
                </div>
                <h2 className="mt-2 truncate text-[11px] font-semibold text-azul-950" title={producto.nombre}>
                  {producto.nombre}
                </h2>
                <p className="mt-0.5 truncate text-[9px] text-azul-400">
                  {disponible > 0 ? `${formatearCantidad(disponible)} disponibles` : 'Agotado'}
                  {ubicacion && ` · ${ubicacion}`}
                </p>
                <div className="mt-auto flex items-center justify-between gap-2 pt-2">
                  <span className="text-xs font-bold text-azul-950">
                    {formatearPesos(Number(producto.precio_evento))}
                  </span>
                  <button
                    type="button"
                    aria-label={`Agregar ${producto.nombre} al carrito`}
                    title="Agregar al carrito"
                    disabled={cantidadEnCarrito >= disponible}
                    onClick={() => agregarAlCarrito(producto)}
                    className="grid size-7 flex-none place-items-center rounded-lg bg-azul-950 text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600 disabled:cursor-not-allowed disabled:bg-azul-300"
                  >
                    <PlusIcon size={15} weight="bold" />
                  </button>
                </div>
              </article>
            )
          })}
          {!productosVisibles.length && (
            <p className="col-span-full rounded-xl border border-dashed border-azul-200 bg-blanco px-4 py-10 text-center text-sm text-azul-500">
              No hay productos en esta categoría.
            </p>
          )}
        </div>
      </section>

      <aside
        aria-label="Carrito de venta actual"
        className="flex min-h-[460px] flex-col overflow-hidden rounded-xl border border-azul-150 bg-blanco xl:sticky xl:top-5 xl:h-[calc(100dvh-7rem)]"
      >
        <header className="flex items-start justify-between border-b border-azul-100 px-3.5 py-3">
          <div>
            <h2 className="text-xs font-bold text-azul-950">Venta actual</h2>
            <p className="mt-1 text-[9px] text-azul-400">Venta en curso · sin guardar</p>
          </div>
          <span className="rounded-full bg-azul-50 px-2 py-1 text-[9px] font-bold text-azul-600">
            {cantidadArticulos} {cantidadArticulos === 1 ? 'artículo' : 'artículos'}
          </span>
        </header>

        <div className="min-h-32 flex-1 divide-y divide-azul-100 overflow-y-auto px-3.5">
          {carrito.map(({ producto, cantidad }) => {
            const stockMaximo = (existenciasPorProducto.get(String(producto.id)) ?? []).reduce(
              (totalStock, existencia) => totalStock + Number(existencia.cantidad_disponible),
              0
            )

            return (
              <div key={producto.id} className="flex items-center gap-2 py-3">
                <div className="size-9 flex-none overflow-hidden rounded-lg">
                  <ImagenProducto producto={producto} />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-[10px] font-semibold text-azul-950">{producto.nombre}</h3>
                  <p className="text-[9px] font-medium text-azul-600">
                    {formatearPesos(Number(producto.precio_evento))}
                  </p>
                </div>
                <div className="flex flex-none items-center gap-1.5">
                  <button
                    type="button"
                    aria-label={`Restar ${producto.nombre}`}
                    onClick={() => cambiarCantidad(producto.id, -1)}
                    className="grid size-6 place-items-center rounded-md border border-azul-150 text-azul-600 hover:bg-azul-50"
                  >
                    <MinusIcon size={12} />
                  </button>
                  <span className="w-3 text-center text-[10px] font-semibold text-azul-950">{cantidad}</span>
                  <button
                    type="button"
                    aria-label={`Sumar ${producto.nombre}`}
                    disabled={cantidad >= stockMaximo}
                    onClick={() => cambiarCantidad(producto.id, 1)}
                    className="grid size-6 place-items-center rounded-md bg-azul-950 text-blanco hover:bg-azul-800 disabled:cursor-not-allowed disabled:bg-azul-300"
                  >
                    <PlusIcon size={12} weight="bold" />
                  </button>
                  <button
                    type="button"
                    aria-label={`Eliminar ${producto.nombre} del carrito`}
                    title="Eliminar del carrito"
                    onClick={() => eliminarDelCarrito(producto.id)}
                    className="grid size-6 place-items-center rounded-md border border-azul-150 text-azul-600 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-600"
                  >
                    <TrashIcon size={12} />
                  </button>
                </div>
              </div>
            )
          })}
          {!carrito.length && (
            <div className="flex h-full min-h-32 flex-col items-center justify-center gap-2 text-center">
              <ShoppingCartSimpleIcon size={24} className="text-azul-300" />
              <p className="text-[11px] font-semibold text-azul-600">El carrito está vacío</p>
              <p className="text-[9px] text-azul-400">Agrega productos para comenzar la venta.</p>
            </div>
          )}
        </div>

        <section className="border-t border-azul-100 px-3.5 py-3">
          <dl className="flex flex-col gap-2 text-[10px]">
            <div className="flex justify-between gap-3 text-azul-500">
              <dt>Subtotal</dt><dd>{formatearPesos(subtotal)}</dd>
            </div>
            <div className="flex justify-between gap-3 text-azul-500">
              <dt>IVA (19%)</dt><dd>{formatearPesos(impuesto)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-azul-500">
              <dt className="flex items-center gap-1.5">
                Descuento
                <label className="sr-only" htmlFor="porcentaje-descuento">Descuento porcentual</label>
                <input
                  id="porcentaje-descuento"
                  aria-label="Descuento porcentual"
                  type="number"
                  min="0"
                  max="100"
                  value={porcentajeDescuento}
                  onChange={(evento) =>
                    setPorcentajeDescuento(String(Math.min(100, Math.max(0, Number(evento.target.value)))))
                  }
                  className="h-6 w-10 rounded border border-azul-150 text-center text-[9px] text-azul-700 outline-none focus:border-azul-600"
                />
                %
              </dt>
              <dd>−{formatearPesos(descuento)}</dd>
            </div>
          </dl>
          <div className="mt-3 flex items-center justify-between border-t border-dashed border-azul-200 pt-2.5">
            <span className="text-sm font-bold text-azul-950">Total</span>
            <span className="text-sm font-bold text-azul-950">{formatearPesos(total)}</span>
          </div>
          <button
            type="button"
            disabled={!carrito.length}
            onClick={cobrar}
            className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-azul-950 px-3 text-[10px] font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600 disabled:cursor-not-allowed disabled:bg-azul-300"
          >
            <PrinterIcon size={14} /> Cobrar e imprimir
          </button>
          {avisoCobro && <p role="status" className="mt-2 text-center text-[9px] text-azul-500">{avisoCobro}</p>}
        </section>
      </aside>
    </div>
  )
}
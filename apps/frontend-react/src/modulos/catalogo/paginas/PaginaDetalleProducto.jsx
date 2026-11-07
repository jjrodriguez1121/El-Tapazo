import { useState } from 'react'
import {
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowUpIcon,
  ArrowsClockwiseIcon,
  ImageIcon,
  PencilSimpleIcon,
  ShoppingCartSimpleIcon,
  TruckIcon,
} from '@phosphor-icons/react'
import { Link, useLocation, useParams } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import Insignia from '@/componentes/ui/Insignia'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import ModalNuevoProducto from '../componentes/ModalNuevoProducto'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'
import { CATEGORIAS_DE_EJEMPLO, PRODUCTOS_DE_EJEMPLO } from '../utilidades/datosDeEjemplo'

const ICONO_POR_MOVIMIENTO = {
  entrada: { Icono: ArrowDownIcon, clase: 'bg-exito-50 text-exito-700' },
  salida: { Icono: ArrowUpIcon, clase: 'bg-error-50 text-error-700' },
  ajuste: { Icono: ArrowsClockwiseIcon, clase: 'bg-azul-50 text-azul-600' },
}

function ImagenDeProducto({ src, className = '' }) {
  return src ? (
    <img src={src} alt="Imagen del producto" className={`h-full w-full object-contain ${className}`} />
  ) : (
    <div
      role="img"
      aria-label="Producto sin imagen"
      className={`grid h-full w-full place-items-center rounded-xl border border-azul-150 bg-azul-50 text-azul-300 ${className}`}
    >
      <ImageIcon size={30} />
    </div>
  )
}

export default function PaginaDetalleProducto() {
  const { productoId } = useParams()
  const { state } = useLocation()
  const catalogo = useCatalogoDeProductos()
  const [mensajeAccion, setMensajeAccion] = useState('')
  const [modalEdicionAbierto, setModalEdicionAbierto] = useState(false)
  const [productoEditado, setProductoEditado] = useState(null)
  const productoDesdeRuta = state?.producto
  const productoDesdeCatalogo = catalogo.data?.productos.find(
    (producto) => String(producto.id) === productoId
  )
  const productoDeEjemplo = PRODUCTOS_DE_EJEMPLO.find(
    (producto) => String(producto.id) === productoId
  )
  const producto = productoEditado ?? productoDesdeRuta ?? productoDesdeCatalogo ?? productoDeEjemplo

  if (!producto && catalogo.isPending) return <EsqueletoDeProductos />

  if (!producto && catalogo.isError) {
    return (
      <section className="flex flex-col gap-4">
        <Link to="/productos" className="inline-flex items-center gap-2 text-sm font-semibold text-azul-600">
          <ArrowLeftIcon size={16} /> Volver a productos
        </Link>
        <Aviso>{mensajeDeError(catalogo.error)}</Aviso>
      </section>
    )
  }

  if (!producto) {
    return (
      <section className="flex flex-col gap-4">
        <Link to="/productos" className="inline-flex items-center gap-2 text-sm font-semibold text-azul-600">
          <ArrowLeftIcon size={16} /> Volver a productos
        </Link>
        <Aviso>No encontramos ese producto en el catálogo.</Aviso>
      </section>
    )
  }

  const existencias =
    producto.existencias ??
    (catalogo.data?.existencias ?? []).filter(
      (existencia) => String(existencia.producto.id) === String(producto.id)
    )
  const stockDisponible = existencias.reduce(
    (total, existencia) => total + Number(existencia.cantidad_disponible),
    0
  )
  const stockMinimo = existencias.reduce(
    (total, existencia) => total + Number(existencia.cantidad_minima ?? 0),
    0
  )
  const estadoStock = stockDisponible <= 0
    ? { etiqueta: 'Sin stock', tono: 'error' }
    : existencias.some((existencia) => existencia.esta_bajo_minimo)
      ? { etiqueta: 'Stock bajo', tono: 'alerta' }
      : { etiqueta: 'En stock', tono: 'exito' }
  const ubicaciones = [...new Set(existencias.map((existencia) => existencia.ubicacion.nombre))]
  const proveedor = producto.proveedor
  const movimientos = producto.movimientos ?? []
  const categorias = catalogo.data?.categorias.length
    ? catalogo.data.categorias
    : CATEGORIAS_DE_EJEMPLO

  function actualizarProducto(datos) {
    const idProducto = producto.id
    const estaBajoMinimo = datos.stockMinimo > 0 && datos.stockActual <= datos.stockMinimo
    setProductoEditado({
      ...producto,
      nombre: datos.nombre,
      sku: datos.sku,
      categoria: datos.categoria,
      unidad: datos.unidad,
      precio_evento: datos.precioVenta,
      imagen: datos.imagen || producto.imagen || '',
      existencias: [
        {
          producto: { id: idProducto },
          ubicacion: { nombre: datos.ubicacion },
          cantidad_disponible: datos.stockActual,
          cantidad_minima: datos.stockMinimo,
          esta_bajo_minimo: estaBajoMinimo,
        },
      ],
    })
    setModalEdicionAbierto(false)
  }

  return (
    <div className="flex flex-col gap-5">
      <Link
        to="/productos"
        state={productoEditado ? { productoActualizado: productoEditado } : undefined}
        className="inline-flex w-fit items-center gap-2 text-xs font-semibold text-azul-600 hover:text-azul-950 focus-visible:outline-2 focus-visible:outline-azul-600"
      >
        <ArrowLeftIcon size={15} /> Volver a productos
      </Link>

      {producto.esDeEjemplo && (
        <p className="-mt-3 text-xs font-semibold text-alerta-700">Detalle con datos de ejemplo</p>
      )}

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="flex min-w-0 flex-col gap-2">
          <div className="aspect-[4/3] overflow-hidden rounded-xl">
            <ImagenDeProducto src={producto.imagen} />
          </div>
          <div className="grid grid-cols-3 gap-2" aria-label="Imágenes adicionales">
            {[0, 1, 2].map((indice) => (
              <div key={indice} className="aspect-[2/1] overflow-hidden rounded-lg">
                <ImagenDeProducto src={producto.imagen} />
              </div>
            ))}
          </div>
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <header>
            <Insignia tono="info">{producto.categoria.nombre}</Insignia>
            <h1 className="mt-2 text-2xl font-bold text-azul-950">{producto.nombre}</h1>
            <p className="mt-1 text-xs font-medium text-azul-400">SKU&nbsp; {producto.sku}</p>
          </header>

          <div className="flex flex-wrap items-center gap-3">
            <p className="text-2xl font-bold text-azul-950">
              {formatearPesos(Number(producto.precio_evento))}
            </p>
            <Insignia tono={estadoStock.tono}>{estadoStock.etiqueta}</Insignia>
          </div>

          <dl className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-xl border border-azul-150 bg-blanco px-3.5 py-3">
              <dt className="text-[11px] text-azul-400">Stock disponible</dt>
              <dd className="mt-1 text-sm font-bold text-azul-950">
                {formatearCantidad(stockDisponible)} {producto.unidad ?? 'unidades'}
              </dd>
            </div>
            <div className="rounded-xl border border-azul-150 bg-blanco px-3.5 py-3">
              <dt className="text-[11px] text-azul-400">Stock mínimo</dt>
              <dd className="mt-1 text-sm font-bold text-azul-950">
                {formatearCantidad(stockMinimo)} {producto.unidad ?? 'unidades'}
              </dd>
            </div>
            <div className="rounded-xl border border-azul-150 bg-blanco px-3.5 py-3">
              <dt className="text-[11px] text-azul-400">Ubicación</dt>
              <dd className="mt-1 text-sm font-bold text-azul-950">
                {ubicaciones.length ? ubicaciones.join(', ') : 'Sin ubicación registrada'}
              </dd>
            </div>
            <div className="rounded-xl border border-azul-150 bg-blanco px-3.5 py-3">
              <dt className="text-[11px] text-azul-400">Unidad de medida</dt>
              <dd className="mt-1 text-sm font-bold text-azul-950">{producto.unidad ?? 'Unidad'}</dd>
            </div>
          </dl>

          {producto.compatibilidad?.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold text-azul-700">Compatibilidad</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {producto.compatibilidad.map((elemento) => (
                  <Insignia key={elemento}>{elemento}</Insignia>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setModalEdicionAbierto(true)}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-azul-950 px-4 text-xs font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
            >
              <PencilSimpleIcon size={15} /> Editar producto
            </button>
            <button
              type="button"
              onClick={() => setMensajeAccion('La venta se conectará en la siguiente etapa.')}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-azul-200 bg-blanco px-4 text-xs font-bold text-azul-800 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-600"
            >
              <ShoppingCartSimpleIcon size={15} /> Agregar a venta
            </button>
          </div>
          {mensajeAccion && <p role="status" className="text-xs font-medium text-azul-600">{mensajeAccion}</p>}
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-2">
        <article className="min-h-36 rounded-xl border border-azul-150 bg-blanco p-4">
          <h2 className="text-sm font-bold text-azul-950">Proveedor</h2>
          {proveedor ? (
            <div className="mt-4 flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-lg bg-azul-50 text-azul-600">
                <TruckIcon size={18} />
              </span>
              <div>
                <p className="text-xs font-bold text-azul-950">{proveedor.razonSocial ?? proveedor.razon_social}</p>
                <p className="mt-0.5 text-[10px] text-azul-400">
                  {proveedor.esDeEjemplo || producto.esDeEjemplo ? 'Proveedor de ejemplo' : 'Proveedor asociado'}
                </p>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-xs text-azul-400">No hay un proveedor asociado a este producto.</p>
          )}
        </article>

        <article className="min-h-36 rounded-xl border border-azul-150 bg-blanco p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-bold text-azul-950">Movimientos recientes</h2>
            {producto.esDeEjemplo && <span className="text-[10px] font-semibold text-alerta-700">Datos de ejemplo</span>}
          </div>
          {movimientos.length ? (
            <ul className="mt-3 divide-y divide-azul-100">
              {movimientos.map((movimiento) => {
                const apariencia = ICONO_POR_MOVIMIENTO[movimiento.tipo] ?? ICONO_POR_MOVIMIENTO.ajuste
                const Icono = apariencia.Icono
                return (
                  <li key={movimiento.id} className="flex items-center gap-2.5 py-2">
                    <span className={`grid size-7 flex-none place-items-center rounded-lg ${apariencia.clase}`}>
                      <Icono size={14} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[11px] font-semibold text-azul-950">
                        {movimiento.titulo}
                      </span>
                      <span className="block truncate text-[9px] text-azul-400">
                        {movimiento.fecha} · {movimiento.referencia}
                      </span>
                    </span>
                    <span className="text-xs font-bold text-azul-600">{movimiento.cantidad}</span>
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="mt-4 text-xs text-azul-400">Todavía no hay movimientos registrados.</p>
          )}
        </article>
      </section>

      {modalEdicionAbierto && (
        <ModalNuevoProducto
          categorias={categorias}
          productoParaEditar={producto}
          existencias={existencias}
          productosExistentes={catalogo.data?.productos ?? PRODUCTOS_DE_EJEMPLO}
          alCrear={actualizarProducto}
          alCerrar={() => setModalEdicionAbierto(false)}
        />
      )}
    </div>
  )
}
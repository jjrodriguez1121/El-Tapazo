import { useState } from 'react'
import {
  ArrowLeftIcon,
  ImageIcon,
  PencilSimpleIcon,
} from '@phosphor-icons/react'
import { Link, useLocation, useParams } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import Insignia from '@/componentes/ui/Insignia'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'
import { clienteApi } from '@/librerias/clienteApi'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import ModalNuevoProducto from '../componentes/ModalNuevoProducto'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

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
  const [modalEdicionAbierto, setModalEdicionAbierto] = useState(false)
  const [productoEditado, setProductoEditado] = useState(null)
  const productoDesdeRuta = state?.producto
  const productoDesdeCatalogo = catalogo.data?.productos.find(
    (producto) => String(producto.id) === productoId
  )
  const producto = productoEditado ?? productoDesdeRuta ?? productoDesdeCatalogo

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
  const categorias = catalogo.data?.categorias ?? []

  async function actualizarProducto(datos) {
    const idProducto = producto.id
    const estaBajoMinimo = datos.stockMinimo > 0 && datos.stockActual <= datos.stockMinimo
    const respuesta = await clienteApi.put(`/catalogo/productos/${idProducto}/`, {
      sku: datos.sku.trim(),
      nombre: datos.nombre.trim(),
      categoria_id: datos.categoria.id,
      costo: producto.costo ?? 0,
      precio_venta: datos.precioVenta,
      margen_ganancia: datos.margenGanancia,
      precio_venta_automatico: datos.precioAutomatico,
      cantidad_disponible: datos.stockActual,
      cantidad_minima: datos.stockMinimo,
      imagen: datos.imagen || '',
    })
    setProductoEditado({
      ...respuesta.data,
      nombre: datos.nombre,
      sku: datos.sku,
      categoria: datos.categoria,
      unidad: datos.unidad,
      imagen: datos.imagen || producto.imagen || '',
      existencias: [
        {
          producto: { id: idProducto },
          ubicacion: { nombre: 'Bodega Principal' },
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
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <header>
            <Insignia tono="info">{producto.categoria.nombre}</Insignia>
            <h1 className="mt-2 text-2xl font-bold text-azul-950">{producto.nombre}</h1>
            <p className="mt-1 text-xs font-medium text-azul-400">SKU&nbsp; {producto.sku}</p>
          </header>

          <div className="flex flex-wrap items-center gap-3">
            <p className="text-2xl font-bold text-azul-950">
              {formatearPesos(Number(producto.precio_venta ?? producto.precio_evento))}
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

          <div>
            <button
              type="button"
              onClick={() => setModalEdicionAbierto(true)}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-azul-950 px-4 text-xs font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
            >
              <PencilSimpleIcon size={15} /> Editar producto
            </button>
          </div>
        </div>
      </section>

      {modalEdicionAbierto && (
        <ModalNuevoProducto
          categorias={categorias}
          productoParaEditar={producto}
          existencias={existencias}
          productosExistentes={catalogo.data?.productos ?? []}
          alCrear={actualizarProducto}
          alCerrar={() => setModalEdicionAbierto(false)}
        />
      )}
    </div>
  )
}
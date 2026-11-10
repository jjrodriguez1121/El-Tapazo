import { useEffect, useState } from 'react'
import {
  CheckCircleIcon,
  PrinterIcon,
  ImageIcon,
  MinusIcon,
  MagnifyingGlassIcon,
  PackageIcon,
  PlusIcon,
  ShoppingCartSimpleIcon,
  TrashIcon,
  WarningCircleIcon,
} from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'
import { mensajeDeError } from '@/utilidades/errores'
import { imprimirComprobanteVenta } from '@/utilidades/imprimirComprobanteVenta'
import { obtenerFechaMinimaVencimiento } from '@/utilidades/fechas'
import { clienteApi } from '@/librerias/clienteApi'
import { crearVenta, listarMetodosPago, obtenerDetalleVenta } from '@/modulos/ventas/api/apiVentas'
import ModalNuevoCliente from '@/modulos/clientes/componentes/ModalNuevoCliente'

import EsqueletoDeProductos from '../componentes/EsqueletoDeProductos'
import { useCatalogoDeProductos } from '../hooks/useCatalogoDeProductos'

function ImagenProducto({ producto }) {
  return producto.imagen ? (
    <img src={producto.imagen} alt="" className="h-full w-full object-cover" />
  ) : (
    <div
      aria-hidden="true"
      className="grid h-full w-full place-items-center text-azul-300"
      style={{
        backgroundImage: 'repeating-linear-gradient(45deg, #f3f5f5 0 7px, #e8ebec 7px 14px)',
      }}
    >
      <ImageIcon size={24} />
    </div>
  )
}

export default function PaginaPuntoDeVenta() {
  const catalogo = useCatalogoDeProductos()
  const [categoriaActiva, setCategoriaActiva] = useState('todas')
  const [busquedaProducto, setBusquedaProducto] = useState('')
  const [carrito, setCarrito] = useState([])
  const [porcentajeDescuento, setPorcentajeDescuento] = useState('5')
  const [avisoCobro, setAvisoCobro] = useState('')
  const [tipoAviso, setTipoAviso] = useState('') // 'exito' | 'error'
  const [tipoPago, setTipoPago] = useState('contado')
  const [estadoEntrega, setEstadoEntrega] = useState('pendiente_entrega')
  const [metodoPago, setMetodoPago] = useState('')
  const [clienteId, setClienteId] = useState('')
  const [fechaVencimiento, setFechaVencimiento] = useState('')
  const [clientes, setClientes] = useState([])
  const [modalClienteAbierto, setModalClienteAbierto] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [metodosPago, setMetodosPago] = useState([])
  const [ventaParaImprimir, setVentaParaImprimir] = useState(null)

  useEffect(() => {
    clienteApi
      .get('/clientes/', { params: { activo: true } })
      .then(({ data }) => {
        const registros = Array.isArray(data) ? data : (data.results ?? [])
        setClientes(registros.filter((cliente) => cliente.activo !== false))
      })
      .catch(() => setClientes([]))
    listarMetodosPago()
      .then((metodos) => {
        setMetodosPago(metodos)
        setMetodoPago(String(metodos[0]?.id ?? ''))
      })
      .catch(() => setMetodosPago([]))
  }, [])

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

  const {
    productos: productosApi,
    categorias: categoriasApi,
    existencias: existenciasApi,
  } = catalogo.data
  const productos = productosApi
  const categorias = categoriasApi
  const existencias = existenciasApi
  const existenciasPorProducto = new Map()

  for (const existencia of existencias) {
    const idProducto = String(existencia.producto.id)
    existenciasPorProducto.set(idProducto, [
      ...(existenciasPorProducto.get(idProducto) ?? []),
      existencia,
    ])
  }

  const terminoBusqueda = busquedaProducto.trim().toLocaleLowerCase()
  const productosVisibles = productos.filter((producto) => {
    const stockDisponible = (existenciasPorProducto.get(String(producto.id)) ?? []).reduce(
      (total, existencia) => total + Number(existencia.cantidad_disponible),
      0
    )
    const coincideCategoria =
      categoriaActiva === 'todas' || String(producto.categoria.id) === categoriaActiva
    const coincideBusqueda =
      !terminoBusqueda ||
      producto.nombre.toLocaleLowerCase().includes(terminoBusqueda) ||
      String(producto.sku ?? '').toLocaleLowerCase().includes(terminoBusqueda)
    return stockDisponible > 0 && coincideCategoria && coincideBusqueda
  })
  const cantidadArticulos = carrito.reduce((total, linea) => total + linea.cantidad, 0)
  const subtotal = carrito.reduce(
    (total, linea) =>
      total +
      Number(linea.producto.precio_venta ?? linea.producto.precio_evento ?? 0) * linea.cantidad,
    0
  )
  const descuento = Math.round(subtotal * (Number(porcentajeDescuento || 0) / 100))
  const totalConDescuento = subtotal - descuento
  const impuesto = Math.round(
    carrito.reduce((totalImpuesto, linea) => {
      const precio = Number(linea.producto.precio_venta ?? linea.producto.precio_evento ?? 0)
      const porcentaje = Number(linea.producto.impuesto?.porcentaje ?? 0)
      const importeLinea = Math.round(precio * linea.cantidad)
      const importeLineaConDescuento =
        subtotal > 0 ? importeLinea - Math.round((importeLinea * descuento) / subtotal) : 0
      if (!porcentaje) return totalImpuesto
      return (
        totalImpuesto + Math.round((importeLineaConDescuento * porcentaje) / (100 + porcentaje))
      )
    }, 0)
  )
  const baseGravable = totalConDescuento - impuesto
  const tasasDeImpuesto = [
    ...new Set(carrito.map((linea) => Number(linea.producto.impuesto?.porcentaje ?? 0))),
  ]
  const etiquetaImpuesto =
    tasasDeImpuesto.length === 1 ? `IVA (${tasasDeImpuesto[0]}%)` : 'IVA (mixto)'
  const total = totalConDescuento

  function agregarAlCarrito(producto) {
    setAvisoCobro('')
    setCarrito((actual) => {
      const lineaExistente = actual.find(
        (linea) => String(linea.producto.id) === String(producto.id)
      )
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

  async function crearCliente(cliente) {
    const partesNombre = cliente.nombre.trim().split(/\s+/)
    const nombre = partesNombre.shift() ?? ''
    const apellido = partesNombre.join(' ')
    const esEstablecimiento = cliente.tipoDocumento.toLowerCase() === 'nit'
    const { data } = await clienteApi.post('/clientes/', {
      tipo_documento: cliente.tipoDocumento.toLowerCase(),
      numero_documento: cliente.documento,
      nombre: esEstablecimiento ? cliente.nombre.trim() : nombre,
      apellido: esEstablecimiento ? '' : apellido,
      fecha_nacimiento: cliente.fechaNacimiento || null,
      telefono: cliente.telefono,
      correo: cliente.correo,
      ciudad: cliente.ciudad,
    })
    setClientes((actuales) => [...actuales, data])
    setClienteId(String(data.id))
  }

  async function cobrar() {
    if (tipoPago === 'credito' && (!clienteId || !fechaVencimiento)) {
      setTipoAviso('error')
      setAvisoCobro('Seleccione el cliente y la fecha de vencimiento para una venta a crédito.')
      return
    }
    if (tipoPago === 'credito' && fechaVencimiento < obtenerFechaMinimaVencimiento()) {
      setTipoAviso('error')
      setAvisoCobro('La fecha de vencimiento debe ser a partir de mañana.')
      return
    }
    setGuardando(true)
    setAvisoCobro('')
    setTipoAviso('')
    try {
      const venta = await crearVenta({
        lineas: carrito.map((linea) => ({
          producto_id: linea.producto.id,
          cantidad: linea.cantidad,
        })),
        tipo_pago: tipoPago,
        estado_entrega: estadoEntrega,
        metodo_pago_id: tipoPago === 'contado' ? Number(metodoPago) : null,
        cliente_id: clienteId ? Number(clienteId) : null,
        fecha_vencimiento: tipoPago === 'credito' ? fechaVencimiento : null,
        descuento_porcentaje: Number(porcentajeDescuento || 0),
      })
      setCarrito([])
      setTipoAviso('exito')
      setAvisoCobro(
        `Venta ${venta.numero_venta} registrada por ${formatearPesos(Number(venta.total))}.`
      )
      const resultadoDetalle = await obtenerDetalleVenta(venta.id).then(
        (detalle) => ({ detalle }),
        (errorDetalle) => ({ error: errorDetalle })
      )
      if (resultadoDetalle.detalle) {
        setVentaParaImprimir(resultadoDetalle.detalle)
      } else {
        setTipoAviso('error')
        setAvisoCobro(
          `La venta ${venta.numero_venta} se registró, pero no fue posible cargar el comprobante: ${mensajeDeError(resultadoDetalle.error)}`
        )
      }
      catalogo.refetch().catch(() => {
        setTipoAviso('error')
        setAvisoCobro(
          `La venta ${venta.numero_venta} se registró, pero no fue posible actualizar el catálogo.`
        )
      })
    } catch (error) {
      setTipoAviso('error')
      setAvisoCobro(mensajeDeError(error))
    } finally {
      setGuardando(false)
    }
  }

  function imprimirVenta() {
    try {
      imprimirComprobanteVenta(ventaParaImprimir)
      setVentaParaImprimir(null)
    } catch (errorImpresion) {
      setTipoAviso('error')
      setAvisoCobro(errorImpresion.message || 'No fue posible preparar el comprobante PDF.')
    }
  }

  return (
    <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_272px]">
      <section className="flex min-w-0 flex-col gap-3.5">
        <header>
          <h1 className="text-titulo font-bold text-azul-950">Punto de venta</h1>
          <p className="mt-1 text-xs font-medium text-azul-400">
            Agrega productos al carrito para registrar la venta
          </p>
        </header>

        <label className="relative block">
          <MagnifyingGlassIcon
            aria-hidden="true"
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-azul-400"
          />
          <input
            type="search"
            aria-label="Buscar productos"
            placeholder="Buscar por nombre o código..."
            value={busquedaProducto}
            onChange={(evento) => setBusquedaProducto(evento.target.value)}
            className="h-10 w-full rounded-lg border border-azul-200 bg-blanco pl-9 pr-3 text-xs text-azul-950 outline-none placeholder:text-azul-400 focus:border-azul-600"
          />
        </label>

        <div
          className="flex gap-2 overflow-x-auto pb-1"
          aria-label="Filtrar productos por categoría"
        >
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
              carrito.find((linea) => String(linea.producto.id) === String(producto.id))
                ?.cantidad ?? 0
            const ubicacion = stockDelProducto
              .map((existencia) => existencia.ubicacion?.nombre)
              .filter(Boolean)
              .join(', ')

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
                <h2
                  className="mt-2 truncate text-[11px] font-semibold text-azul-950"
                  title={producto.nombre}
                >
                  {producto.nombre}
                </h2>
                <p className="mt-0.5 truncate text-[9px] text-azul-400">
                  {disponible > 0 ? `${formatearCantidad(disponible)} disponibles` : 'Agotado'}
                  {ubicacion && ` · ${ubicacion}`}
                </p>
                <div className="mt-auto flex items-center justify-between gap-2 pt-2">
                  <span className="text-xs font-bold text-azul-950">
                    {formatearPesos(Number(producto.precio_venta ?? producto.precio_evento ?? 0))}
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
              {busquedaProducto.trim()
                ? 'No se encontraron productos disponibles con esa búsqueda.'
                : 'No hay productos disponibles con stock en esta categoría.'}
            </p>
          )}
        </div>
      </section>

      <aside
        aria-label="Carrito de venta actual"
        className="flex min-h-[460px] flex-col rounded-xl border border-azul-150 bg-blanco xl:sticky xl:top-5 xl:max-h-[calc(100dvh-5rem)]"
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
                  <h3 className="truncate text-[10px] font-semibold text-azul-950">
                    {producto.nombre}
                  </h3>
                  <p className="text-[9px] font-medium text-azul-600">
                    {formatearPesos(Number(producto.precio_venta ?? producto.precio_evento ?? 0))}
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
                  <span className="w-3 text-center text-[10px] font-semibold text-azul-950">
                    {cantidad}
                  </span>
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

        <section className="overflow-y-auto border-t border-azul-100 px-3.5 py-3">
          <dl className="flex flex-col gap-2 text-[10px]">
            <div className="flex justify-between gap-3 text-azul-500">
              <dt>Subtotal</dt>
              <dd>{formatearPesos(baseGravable)}</dd>
            </div>
            <div className="flex justify-between gap-3 text-azul-500">
              <dt>{etiquetaImpuesto}</dt>
              <dd>{formatearPesos(impuesto)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-azul-500">
              <dt className="flex items-center gap-1.5">
                Descuento
                <label className="sr-only" htmlFor="porcentaje-descuento">
                  Descuento porcentual
                </label>
                <input
                  id="porcentaje-descuento"
                  aria-label="Descuento porcentual"
                  type="number"
                  min="0"
                  max="100"
                  value={porcentajeDescuento}
                  onChange={(evento) =>
                    setPorcentajeDescuento(
                      String(Math.min(100, Math.max(0, Number(evento.target.value))))
                    )
                  }
                  className="h-6 w-10 rounded border border-azul-150 text-center text-[9px] text-azul-700 outline-none focus:border-azul-600"
                />
                %
              </dt>
              <dd>
                <span aria-hidden="true">−</span>
                <span>{formatearPesos(descuento)}</span>
              </dd>
            </div>
          </dl>
          <div className="mt-3 flex items-center justify-between border-t border-dashed border-azul-200 pt-2.5">
            <span className="text-sm font-bold text-azul-950">Total</span>
            <span className="text-sm font-bold text-azul-950">{formatearPesos(total)}</span>
          </div>
          <div className="mt-3 grid gap-2">
            <label className="text-[10px] font-bold text-azul-600">
              Tipo de pago
              <select
                value={tipoPago}
                onChange={(evento) => setTipoPago(evento.target.value)}
                className="mt-1 h-8 w-full rounded-lg border border-azul-200 px-2 text-xs"
              >
                <option value="contado">Contado</option>
                <option value="credito">Crédito</option>
              </select>
            </label>
            <label className="text-[10px] font-bold text-azul-600">
              Estado de entrega
              <select
                value={estadoEntrega}
                onChange={(evento) => setEstadoEntrega(evento.target.value)}
                className="mt-1 h-8 w-full rounded-lg border border-azul-200 px-2 text-xs"
              >
                <option value="pendiente_entrega">Pendiente de entrega</option>
                <option value="entregada">Entregada</option>
              </select>
            </label>
            {tipoPago === 'contado' ? (
              <label className="text-[10px] font-bold text-azul-600">
                Medio de pago
                <select
                  value={metodoPago}
                  onChange={(evento) => setMetodoPago(evento.target.value)}
                  className="mt-1 h-8 w-full rounded-lg border border-azul-200 px-2 text-xs"
                >
                  {metodosPago.map((metodo) => (
                    <option key={metodo.id} value={metodo.id}>
                      {metodo.nombre}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="text-[10px] font-bold text-azul-600">
              Cliente
              <select
                value={clienteId}
                onChange={(evento) => {
                  if (evento.target.value === 'nuevo') {
                    setClienteId('')
                    setModalClienteAbierto(true)
                    return
                  }
                  setClienteId(evento.target.value)
                }}
                className="mt-1 h-8 w-full rounded-lg border border-azul-200 px-2 text-xs"
              >
                <option value="">Seleccione...</option>
                {clientes.map((cliente) => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nombre} {cliente.apellido}
                  </option>
                ))}
                <option value="nuevo">+ Nuevo cliente</option>
              </select>
            </label>
            {tipoPago === 'credito' && (
              <div>
                <label className="text-[10px] font-bold text-azul-600">
                  Vencimiento
                  <input
                    required
                    type="date"
                    min={obtenerFechaMinimaVencimiento()}
                    value={fechaVencimiento}
                    aria-invalid={
                      Boolean(fechaVencimiento) &&
                      fechaVencimiento < obtenerFechaMinimaVencimiento()
                    }
                    onChange={(evento) => {
                      setFechaVencimiento(evento.target.value)
                      setAvisoCobro('')
                    }}
                    className="mt-1 h-8 w-full rounded-lg border border-azul-200 px-2 text-xs aria-[invalid=true]:border-error-600"
                  />
                </label>
                <p className="mt-1 text-[9px] font-normal text-azul-500">
                  Selecciona mañana o una fecha posterior.
                </p>
              </div>
            )}
          </div>
          {modalClienteAbierto && (
            <ModalNuevoCliente
              alCerrar={() => setModalClienteAbierto(false)}
              alGuardar={crearCliente}
              clientesExistentes={clientes.map((cliente) => ({
                tipo: cliente.tipo_documento === 'nit' ? 'establecimiento' : 'persona',
                tipoDocumento: cliente.tipo_documento,
                documento: cliente.numero_documento,
              }))}
            />
          )}
          <button
            type="button"
            disabled={!carrito.length || guardando}
            onClick={cobrar}
            className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-azul-950 px-3 text-[10px] font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600 disabled:cursor-not-allowed disabled:bg-azul-300"
          >
            <CheckCircleIcon size={14} weight="bold" />{' '}
            {guardando ? 'Registrando...' : 'Finalizar Venta'}
          </button>
          {avisoCobro && (
            <div
              role="status"
              className={`mt-2 flex items-center gap-1.5 rounded-lg p-2 text-[10px] font-semibold ${
                tipoAviso === 'exito'
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {tipoAviso === 'exito' ? (
                <CheckCircleIcon size={14} weight="fill" className="flex-none text-green-500" />
              ) : (
                <WarningCircleIcon size={14} weight="fill" className="flex-none text-red-500" />
              )}
              {avisoCobro}
            </div>
          )}
          {ventaParaImprimir && (
            <div className="mt-3 rounded-lg border border-exito-200 bg-exito-50 p-3">
              <p className="text-[11px] font-semibold text-exito-800">
                Venta {ventaParaImprimir.numero_venta} registrada correctamente.
              </p>
              <p className="mt-1 text-[10px] text-exito-700">
                ¿Deseas imprimir o guardar el comprobante en PDF?
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setVentaParaImprimir(null)}
                  className="h-8 rounded-lg border border-exito-300 bg-blanco px-3 text-[10px] font-semibold text-exito-800 hover:bg-exito-100"
                >
                  Ahora no
                </button>
                <button
                  type="button"
                  onClick={imprimirVenta}
                  className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-exito-700 px-3 text-[10px] font-semibold text-blanco hover:bg-exito-800"
                >
                  <PrinterIcon size={14} />
                  Imprimir / Guardar PDF
                </button>
              </div>
            </div>
          )}
        </section>
      </aside>
    </div>
  )
}

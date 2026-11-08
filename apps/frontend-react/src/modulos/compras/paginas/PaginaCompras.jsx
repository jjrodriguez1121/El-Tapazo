import { useEffect, useState } from 'react'
import { PlusIcon, TrashIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import { clienteApi } from '@/librerias/clienteApi'
import { formatearPesos } from '@/utilidades/formatos'
import { crearCompra, listarCompras } from '../api/apiCompras'
import { listarMetodosPago } from '@/modulos/ventas/api/apiVentas'
import ModalDetalleCompra from '../componentes/ModalDetalleCompra'

const lineaVacia = () => ({
  tipo: 'existente',
  productoId: '',
  sku: '',
  nombre: '',
  categoriaId: '',
  impuestoId: '',
  cantidad: 1,
  costoUnitario: '',
  descuento: 0,
})

export default function PaginaCompras() {
  const [compras, setCompras] = useState([])
  const [productos, setProductos] = useState([])
  const [proveedores, setProveedores] = useState([])
  const [categorias, setCategorias] = useState([])
  const [impuestos, setImpuestos] = useState([])
  const [metodosPago, setMetodosPago] = useState([])
  const [lineas, setLineas] = useState([lineaVacia()])
  const [datos, setDatos] = useState({
    proveedorId: '',
    numeroFactura: '',
    condicionPago: 'CONTADO',
    metodoPagoId: '',
    fechaVencimiento: '',
  })
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')
  const [compraDetalleId, setCompraDetalleId] = useState(null)

  async function cargarDatos() {
    setCargando(true)
    try {
      const [listaCompras, listaProductos, listaProveedores, listaCategorias, listaImpuestos, listaMetodosPago] = await Promise.all([
        listarCompras(),
        clienteApi.get('/catalogo/productos/?activo=true'),
        clienteApi.get('/catalogo/proveedores/?activo=true'),
        clienteApi.get('/catalogo/categorias/?activa=true'),
        clienteApi.get('/catalogo/impuestos/'),
        listarMetodosPago(),
      ])
      setCompras(listaCompras)
      setProductos(Array.isArray(listaProductos.data) ? listaProductos.data : listaProductos.data.results ?? [])
      setProveedores(Array.isArray(listaProveedores.data) ? listaProveedores.data : listaProveedores.data.results ?? [])
      setCategorias(Array.isArray(listaCategorias.data) ? listaCategorias.data : listaCategorias.data.results ?? [])
      setImpuestos(Array.isArray(listaImpuestos.data) ? listaImpuestos.data : listaImpuestos.data.results ?? [])
      setMetodosPago(listaMetodosPago)
      setDatos((actual) => ({ ...actual, metodoPagoId: actual.metodoPagoId || String(listaMetodosPago[0]?.id ?? '') }))
    } catch (err) {
      setError(err.response?.data?.detail ?? 'No fue posible cargar los datos de compras.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { cargarDatos() }, [])

  function cambiarLinea(indice, campo, valor) {
    setLineas((actuales) => actuales.map((linea, posicion) =>
      posicion === indice ? { ...linea, [campo]: valor } : linea
    ))
  }

  async function guardar(evento) {
    evento.preventDefault()
    setGuardando(true)
    setError('')
    try {
      const detalles = lineas.map((linea) => ({
        ...(linea.tipo === 'existente'
          ? { producto_id: Number(linea.productoId) }
          : {
              producto_nuevo: {
                sku: linea.sku.trim(),
                nombre: linea.nombre.trim(),
                categoria_id: Number(linea.categoriaId),
                impuesto_id: Number(linea.impuestoId),
              },
            }),
        cantidad: Number(linea.cantidad),
        costo_unitario: Number(linea.costoUnitario),
        descuento: Number(linea.descuento || 0),
      }))
      await crearCompra({
        proveedor_id: Number(datos.proveedorId),
        numero_factura: datos.numeroFactura,
        condicion_pago: datos.condicionPago,
        metodo_pago_id: datos.condicionPago === 'CONTADO' ? Number(datos.metodoPagoId) : null,
        fecha_vencimiento: datos.fechaVencimiento || null,
        estado: 'RECIBIDA',
        detalles,
      })
      setDatos((actual) => ({ ...actual, numeroFactura: '', fechaVencimiento: '' }))
      setLineas([lineaVacia()])
      await cargarDatos()
    } catch (err) {
      setError(err.response?.data?.detail ?? JSON.stringify(err.response?.data ?? 'No fue posible registrar la compra.'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-titulo font-bold text-azul-950">Compras</h1>
        <p className="mt-1 text-sm text-azul-500">Registro de mercancía recibida y nuevos productos. El IVA seleccionado es informativo y no modifica el total de la compra.</p>
      </header>

      {error && <Aviso>{error}</Aviso>}

      <form onSubmit={guardar} className="rounded-xl border border-azul-150 bg-blanco p-5">
        <h2 className="mb-4 text-lg font-bold text-azul-950">Nueva compra</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700">
            Proveedor
            <select required value={datos.proveedorId} onChange={(e) => setDatos({ ...datos, proveedorId: e.target.value })} className="h-10 rounded-lg border border-azul-200 px-3 text-sm">
              <option value="">Seleccione...</option>
              {proveedores.map((proveedor) => <option key={proveedor.id} value={proveedor.id}>{proveedor.razon_social}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700">
            Factura
            <input value={datos.numeroFactura} onChange={(e) => setDatos({ ...datos, numeroFactura: e.target.value })} className="h-10 rounded-lg border border-azul-200 px-3 text-sm" />
          </label>
          <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700">
            Pago
            <select value={datos.condicionPago} onChange={(e) => setDatos({ ...datos, condicionPago: e.target.value })} className="h-10 rounded-lg border border-azul-200 px-3 text-sm">
              <option value="CONTADO">Contado</option>
              <option value="CREDITO">Crédito</option>
            </select>
          </label>
          {datos.condicionPago === 'CREDITO' && (
            <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700">
              Fecha de vencimiento
              <input
                required
                type="date"
                value={datos.fechaVencimiento}
                onChange={(e) => setDatos({ ...datos, fechaVencimiento: e.target.value })}
                className="h-10 rounded-lg border border-azul-200 px-3 text-sm"
              />
            </label>
          )}
          {datos.condicionPago === 'CONTADO' && (
            <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700">
              Medio de pago
              <select required value={datos.metodoPagoId} onChange={(e) => setDatos({ ...datos, metodoPagoId: e.target.value })} className="h-10 rounded-lg border border-azul-200 px-3 text-sm">
                <option value="">Seleccione...</option>
                {metodosPago.map((metodo) => <option key={metodo.id} value={metodo.id}>{metodo.nombre}</option>)}
              </select>
            </label>
          )}
        </div>

        <div className="mt-5 flex flex-col gap-3">
          {lineas.map((linea, indice) => (
            <section key={indice} className="grid gap-3 rounded-lg border border-azul-100 bg-azul-50/40 p-3 md:grid-cols-12">
              <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700 md:col-span-2">
                Tipo
                <select value={linea.tipo} onChange={(e) => cambiarLinea(indice, 'tipo', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm">
                  <option value="existente">Producto existente</option>
                  <option value="nuevo">Producto nuevo</option>
                </select>
              </label>
              {linea.tipo === 'existente' ? (
                <>
                  <label className="flex flex-col gap-1 text-xs font-semibold text-azul-700 md:col-span-3">
                    Producto
                    <select required value={linea.productoId} onChange={(e) => cambiarLinea(indice, 'productoId', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm">
                      <option value="">Seleccione...</option>
                      {productos.map((producto) => <option key={producto.id} value={producto.id}>{producto.sku} · {producto.nombre}</option>)}
                    </select>
                  </label>
                  <div className="flex flex-col justify-end text-xs font-semibold text-azul-700 md:col-span-2">
                    Tarifa informativa
                    <span className="flex h-9 items-center rounded-lg border border-azul-150 bg-blanco px-2 text-sm font-normal text-azul-600">
                      {productos.find((producto) => String(producto.id) === String(linea.productoId))?.impuesto
                        ? `${productos.find((producto) => String(producto.id) === String(linea.productoId)).impuesto.nombre} · ${productos.find((producto) => String(producto.id) === String(linea.productoId)).impuesto.porcentaje}%`
                        : 'Sin tarifa asignada'}
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <input required aria-label="SKU del producto nuevo" placeholder="SKU" value={linea.sku} onChange={(e) => cambiarLinea(indice, 'sku', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm md:col-span-2" />
                  <input required aria-label="Nombre del producto nuevo" placeholder="Nombre" value={linea.nombre} onChange={(e) => cambiarLinea(indice, 'nombre', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm md:col-span-2" />
                  <select required aria-label="Categoría del producto nuevo" value={linea.categoriaId} onChange={(e) => cambiarLinea(indice, 'categoriaId', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm md:col-span-2">
                    <option value="">Categoría...</option>
                    {categorias.map((categoria) => <option key={categoria.id} value={categoria.id}>{categoria.nombre}</option>)}
                  </select>
                  <select required aria-label="Tarifa de IVA" value={linea.impuestoId} onChange={(e) => cambiarLinea(indice, 'impuestoId', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm md:col-span-2">
                    <option value="">Tarifa de IVA...</option>
                    {impuestos.map((impuesto) => <option key={impuesto.id} value={impuesto.id}>{impuesto.nombre} · {impuesto.porcentaje}%</option>)}
                  </select>
                </>
              )}
              <input required type="number" min="1" aria-label="Cantidad" placeholder="Cant." value={linea.cantidad} onChange={(e) => cambiarLinea(indice, 'cantidad', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm" />
              <input required type="number" min="0" step="0.01" aria-label="Costo unitario" placeholder="Costo" value={linea.costoUnitario} onChange={(e) => cambiarLinea(indice, 'costoUnitario', e.target.value)} className="h-9 rounded-lg border border-azul-200 px-2 text-sm" />
              <button type="button" aria-label="Eliminar línea" onClick={() => setLineas((actuales) => actuales.filter((_, i) => i !== indice))} className="grid size-9 place-items-center rounded-lg text-error-600 hover:bg-error-50" disabled={lineas.length === 1}><TrashIcon size={18} /></button>
            </section>
          ))}
        </div>
        <button type="button" onClick={() => setLineas((actuales) => [...actuales, lineaVacia()])} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-azul-200 px-3 py-2 text-xs font-bold text-azul-700">
          <PlusIcon size={16} /> Agregar producto
        </button>
        <button type="submit" disabled={guardando || cargando || !proveedores.length} className="mt-4 block rounded-lg bg-azul-950 px-5 py-2.5 text-sm font-bold text-blanco disabled:opacity-50">
          {guardando ? 'Guardando...' : 'Registrar compra'}
        </button>
      </form>

      <section className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
        <h2 className="border-b border-azul-100 px-4 py-3 text-sm font-bold text-azul-950">Compras registradas</h2>
        <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-azul-50 text-xs uppercase text-azul-500">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Compra</th>
                <th className="px-4 py-3">Proveedor</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Pago</th>
                <th className="px-4 py-3 text-center">Productos</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-center">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {compras.map((compra) => (
                <tr key={compra.id} className="border-t border-azul-100">
                  <td className="px-4 py-3 text-xs text-azul-500">
                    {compra.fecha_compra
                      ? new Intl.DateTimeFormat('es-CO', {
                          dateStyle: 'medium',
                          timeStyle: 'short',
                        }).format(new Date(compra.fecha_compra))
                      : 'N/D'}
                  </td>
                  <td className="px-4 py-3 font-semibold text-azul-950">{compra.numero_compra}</td>
                  <td className="px-4 py-3">{compra.proveedor_nombre}</td>
                  <td className="px-4 py-3">{compra.estado}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${compra.condicion_pago === 'CONTADO' ? 'bg-exito-50 text-exito-700' : 'bg-alerta-50 text-alerta-700'}`}>
                      {compra.condicion_pago === 'CONTADO' ? 'Contado' : 'Crédito'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-azul-600">{compra.detalles?.length ?? 0}</td>
                  <td className="px-4 py-3 text-right font-bold text-azul-950">{formatearPesos(Number(compra.total || 0))}</td>
                  <td className="px-4 py-3 text-center">
                    <button type="button" onClick={() => setCompraDetalleId(compra.id)} className="rounded-lg border border-azul-200 px-3 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-50">
                      Ver detalle
                    </button>
                  </td>
                </tr>
              ))}
              {!compras.length && <tr><td colSpan={8} className="px-4 py-10 text-center text-azul-400">Todavía no hay compras registradas.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
      {compraDetalleId && (
        <ModalDetalleCompra compraId={compraDetalleId} alCerrar={() => setCompraDetalleId(null)} />
      )}
    </div>
  )
}

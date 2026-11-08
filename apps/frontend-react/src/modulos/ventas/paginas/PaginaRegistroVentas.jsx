import { useEffect, useState } from 'react'
import {
  CalendarIcon,
  DownloadSimpleIcon,
  ReceiptIcon,
  ShoppingCartSimpleIcon,
} from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import ConfirmacionAccion from '@/componentes/ui/ConfirmacionAccion'
import FiltroRangoFechas from '@/componentes/ui/FiltroRangoFechas'
import { RUTAS } from '@/configuracion/rutas'
import { estaEnRangoDeFechas } from '@/utilidades/fechas'
import { imprimirReportePdf } from '@/utilidades/exportarReportePdf'
import { formatearPesos } from '@/utilidades/formatos'
import { confirmarEntregaVenta, listarVentas } from '../api/apiVentas'
import ModalDetalleVenta from '../componentes/ModalDetalleVenta'

const TONOS_ESTADO = {
  pagada: 'bg-exito-50 text-exito-700',
  pendiente: 'bg-alerta-50 text-alerta-700',
  anulada: 'bg-error-50 text-error-700',
  PAGADA: 'bg-exito-50 text-exito-700',
  PENDIENTE: 'bg-alerta-50 text-alerta-700',
  ANULADA: 'bg-error-50 text-error-700',
}

const TONOS_ENTREGA = {
  pendiente_entrega: 'bg-alerta-50 text-alerta-700',
  entregada: 'bg-exito-50 text-exito-700',
  anulada: 'bg-error-50 text-error-700',
}

const ETIQUETAS_ENTREGA = {
  pendiente_entrega: 'Pendiente de entrega',
  entregada: 'Entregada',
  anulada: 'Anulada',
}

export default function PaginaRegistroVentas() {
  const [ventas, setVentas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [filtroTexto, setFiltroTexto] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [filtroTipoPago, setFiltroTipoPago] = useState('todos')
  const [filtroEntrega, setFiltroEntrega] = useState('todos')
  const [rangoFechas, setRangoFechas] = useState({ desde: '', hasta: '' })
  const [ventaDetalleId, setVentaDetalleId] = useState(null)
  const [ventaParaEntregar, setVentaParaEntregar] = useState(null)
  const [procesandoEntrega, setProcesandoEntrega] = useState(false)

  async function marcarComoEntregada() {
    if (!ventaParaEntregar) return
    setProcesandoEntrega(true)
    setError('')
    try {
      await confirmarEntregaVenta(ventaParaEntregar.id)
      setVentaParaEntregar(null)
      await cargar()
    } catch (errorSolicitud) {
      setError(
        errorSolicitud.response?.data?.[0] ?? 'No fue posible actualizar el estado de entrega.'
      )
      setVentaParaEntregar(null)
    } finally {
      setProcesandoEntrega(false)
    }
  }

  async function cargar() {
    setCargando(true)
    setError('')
    try {
      const data = await listarVentas()
      setVentas(data)
    } catch {
      setError('No fue posible cargar el registro de ventas.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [])

  const ventasFiltradas = ventas.filter((v) => {
    const coincideFecha = estaEnRangoDeFechas(v.fecha_venta, rangoFechas.desde, rangoFechas.hasta)
    const coincideEstado = filtroEstado === 'todos' || v.estado === filtroEstado
    const coincideTipoPago = filtroTipoPago === 'todos' || v.tipo_pago === filtroTipoPago
    const estadoEntrega = v.estado_entrega ?? 'pendiente_entrega'
    const coincideEntrega = filtroEntrega === 'todos' || estadoEntrega === filtroEntrega
    const texto = filtroTexto.toLowerCase().trim()
    const coincideTexto =
      !texto ||
      v.numero_venta.toLowerCase().includes(texto) ||
      v.cliente_nombre.toLowerCase().includes(texto) ||
      (v.vendedor && v.vendedor.toLowerCase().includes(texto))
    return coincideFecha && coincideEstado && coincideTipoPago && coincideEntrega && coincideTexto
  })

  function descargarReporte() {
    setError('')
    try {
      const fechaVenta = new Intl.DateTimeFormat('es-CO', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
      imprimirReportePdf({
        titulo: 'Registro de ventas',
        descripcion: `Fecha de venta: ${rangoFechas.desde || 'sin límite'} a ${rangoFechas.hasta || 'sin límite'}. Se incluyen los filtros seleccionados en el listado.`,
        columnas: [
          'Fecha',
          'Venta',
          'Cliente',
          'Tipo de pago',
          'Estado de pago',
          'Entrega',
          'Ítems',
          'Total',
        ],
        filas: ventasFiltradas.map((venta) => [
          fechaVenta.format(new Date(venta.fecha_venta)),
          venta.numero_venta,
          venta.cliente_nombre,
          venta.tipo_pago === 'contado' ? 'Contado' : 'Crédito',
          String(venta.estado).toUpperCase(),
          ETIQUETAS_ENTREGA[venta.estado_entrega] ?? 'Pendiente de entrega',
          venta.cantidad_items,
          formatearPesos(Number(venta.total)),
        ]),
      })
    } catch (errorReporte) {
      setError(errorReporte.message || 'No fue posible preparar el reporte PDF.')
    }
  }

  function estaPendienteDeEntrega(venta) {
    return !venta.estado_entrega || venta.estado_entrega === 'pendiente_entrega'
  }

  const ventasVigentes = ventasFiltradas.filter((venta) => venta.estado !== 'anulada')
  const totalVendido = ventasVigentes.reduce((total, v) => total + Number(v.total || 0), 0)
  const ventasContado = ventasVigentes.filter((v) => v.tipo_pago === 'contado').length
  const ventasCredito = ventasVigentes.filter((v) => v.tipo_pago === 'credito').length

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-titulo font-bold text-azul-950">Registro de Ventas</h1>
          <p className="mt-1 text-sm text-azul-500">
            Historial de ventas realizadas en el negocio, facturas y tickets emitidos.
          </p>
        </div>
        <Link
          to={RUTAS.puntoDeVenta}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-azul-950 px-4 py-2.5 text-sm font-semibold text-blanco shadow-sm hover:bg-azul-800"
        >
          <ShoppingCartSimpleIcon size={18} />
          Ir al punto de venta
        </Link>
      </header>

      {error && <Aviso>{error}</Aviso>}

      <section className="grid gap-3 sm:grid-cols-3" aria-label="Resumen de ventas">
        <Resumen
          Icono={ReceiptIcon}
          etiqueta="Total facturado"
          valor={formatearPesos(totalVendido)}
        />
        <Resumen
          Icono={CalendarIcon}
          etiqueta="Ventas registradas"
          valor={String(ventasVigentes.length)}
        />
        <Resumen
          Icono={ReceiptIcon}
          etiqueta="Contado / Crédito"
          valor={`${ventasContado} / ${ventasCredito}`}
        />
      </section>

      <section className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
        <div className="flex flex-col gap-3 border-b border-azul-100 p-4">
          <h2 className="text-sm font-bold text-azul-950">Ventas registradas</h2>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <FiltroRangoFechas
              titulo="Filtrar por fecha de venta"
              desde={rangoFechas.desde}
              hasta={rangoFechas.hasta}
              alCambiar={setRangoFechas}
            />
            <button
              type="button"
              onClick={descargarReporte}
              disabled={cargando}
              title="Se abrirá la impresión del navegador; selecciona Guardar como PDF."
              className="inline-flex h-9 items-center gap-2 rounded-lg bg-azul-950 px-3 text-xs font-semibold text-blanco hover:bg-azul-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <DownloadSimpleIcon size={16} />
              Descargar PDF
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="search"
              placeholder="Buscar por número o cliente..."
              value={filtroTexto}
              onChange={(e) => setFiltroTexto(e.target.value)}
              className="h-9 w-60 rounded-lg border border-azul-200 px-3 text-xs text-azul-950 outline-none focus:border-azul-600"
            />
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
            >
              <option value="todos">Todos los estados</option>
              <option value="pagada">Pagada</option>
              <option value="pendiente">Pendiente</option>
              <option value="anulada">Anulada</option>
            </select>
            <select
              aria-label="Filtrar por tipo de pago"
              value={filtroTipoPago}
              onChange={(e) => setFiltroTipoPago(e.target.value)}
              className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
            >
              <option value="todos">Todos los pagos</option>
              <option value="contado">Contado</option>
              <option value="credito">Crédito</option>
            </select>
            <select
              aria-label="Filtrar por estado de entrega"
              value={filtroEntrega}
              onChange={(e) => setFiltroEntrega(e.target.value)}
              className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
            >
              <option value="todos">Todas las entregas</option>
              <option value="pendiente_entrega">Pendiente de entrega</option>
              <option value="entregada">Entregada</option>
              <option value="anulada">Anulada</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[840px] text-left text-sm">
            <thead className="bg-azul-50 text-xs uppercase text-azul-500">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Venta</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Tipo pago</th>
                <th className="px-4 py-3">Pago</th>
                <th className="px-4 py-3">Entrega</th>
                <th className="px-4 py-3 text-center">Ítems</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ventasFiltradas.map((venta) => (
                <tr key={venta.id} className="border-t border-azul-100 hover:bg-azul-50/30">
                  <td className="px-4 py-3 text-xs font-medium text-azul-500">
                    {new Intl.DateTimeFormat('es-CO', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }).format(new Date(venta.fecha_venta))}
                  </td>
                  <td className="px-4 py-3 font-semibold text-azul-950">{venta.numero_venta}</td>
                  <td className="px-4 py-3 text-azul-700">{venta.cliente_nombre}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                        venta.tipo_pago === 'contado'
                          ? 'bg-exito-50 text-exito-700'
                          : 'bg-alerta-50 text-alerta-700'
                      }`}
                    >
                      {venta.tipo_pago === 'contado' ? 'Contado' : 'Crédito'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                        TONOS_ESTADO[venta.estado] ?? 'bg-azul-50 text-azul-700'
                      }`}
                    >
                      {String(venta.estado).toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                        TONOS_ENTREGA[venta.estado_entrega] ?? 'bg-azul-50 text-azul-700'
                      }`}
                    >
                      {ETIQUETAS_ENTREGA[venta.estado_entrega] ?? 'Pendiente de entrega'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center font-medium text-azul-600">
                    {venta.cantidad_items}
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-azul-950">
                    {formatearPesos(Number(venta.total))}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center gap-2">
                      {estaPendienteDeEntrega(venta) && (
                        <button
                          type="button"
                          onClick={() => setVentaParaEntregar(venta)}
                          className="rounded-lg bg-exito-700 px-3 py-1.5 text-xs font-semibold text-blanco hover:bg-exito-800"
                        >
                          Marcar entregada
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => setVentaDetalleId(venta.id)}
                        className="rounded-lg border border-azul-200 px-3 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-50"
                      >
                        Ver detalle
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!cargando && !ventasFiltradas.length && (
                <tr>
                  <td colSpan={9} className="px-4 py-10 text-center text-azul-400">
                    {ventas.length === 0
                      ? 'Todavía no hay ventas registradas.'
                      : 'No se encontraron ventas con los filtros seleccionados.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {cargando && (
          <p className="px-4 py-10 text-center text-sm text-azul-400">Cargando ventas...</p>
        )}
      </section>

      {ventaDetalleId && (
        <ModalDetalleVenta
          ventaId={ventaDetalleId}
          alCerrar={() => setVentaDetalleId(null)}
          alActualizar={cargar}
        />
      )}
      {ventaParaEntregar && (
        <ConfirmacionAccion
          titulo="Confirmar entrega"
          descripcion={`¿Confirmas que la venta ${ventaParaEntregar.numero_venta} ya fue entregada a ${ventaParaEntregar.cliente_nombre}? Esta acción actualizará su estado de entrega.`}
          textoConfirmar="Confirmar entrega"
          variante="positiva"
          procesando={procesandoEntrega}
          alConfirmar={marcarComoEntregada}
          alCancelar={() => setVentaParaEntregar(null)}
        />
      )}
    </div>
  )
}

function Resumen({ Icono, etiqueta, valor }) {
  return (
    <article className="rounded-xl border border-azul-150 bg-blanco p-4">
      <div className="flex items-center gap-3">
        <div className="grid size-10 place-items-center rounded-lg bg-azul-50 text-azul-700">
          <Icono size={20} />
        </div>
        <div>
          <p className="text-xs font-semibold text-azul-400">{etiqueta}</p>
          <p className="mt-1 text-lg font-bold text-azul-950">{valor}</p>
        </div>
      </div>
    </article>
  )
}

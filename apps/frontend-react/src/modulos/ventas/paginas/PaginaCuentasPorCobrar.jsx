import { useEffect, useState } from 'react'
import { CalendarIcon, DownloadSimpleIcon, HandCoinsIcon, WalletIcon } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import FiltroRangoFechas from '@/componentes/ui/FiltroRangoFechas'
import { clienteApi } from '@/librerias/clienteApi'
import useFiltroPersistente from '@/hooks/useFiltroPersistente'
import { estaEnRangoDeFechas } from '@/utilidades/fechas'
import { imprimirReportePdf } from '@/utilidades/exportarReportePdf'
import { imprimirComprobanteVenta } from '@/utilidades/imprimirComprobanteVenta'
import { formatearFechaCorta, formatearPesos } from '@/utilidades/formatos'
import { obtenerDetalleVenta } from '../api/apiVentas'
import ModalDetalleVenta from '../componentes/ModalDetalleVenta'

const TONOS_ESTADO = {
  pendiente: 'bg-alerta-50 text-alerta-700',
  parcial: 'bg-alerta-50 text-alerta-700',
  vencida: 'bg-error-50 text-error-700',
  PENDIENTE: 'bg-alerta-50 text-alerta-700',
  PARCIAL: 'bg-alerta-50 text-alerta-700',
  VENCIDA: 'bg-error-50 text-error-700',
}

const TONOS_ENTREGA = {
  pendiente_entrega: 'bg-alerta-50 text-alerta-700',
  entregada: 'bg-exito-50 text-exito-700',
}

const ETIQUETAS_ENTREGA = {
  pendiente_entrega: 'Pendiente de entrega',
  entregada: 'Entregada',
}

export default function PaginaCuentasPorCobrar() {
  const navegar = useNavigate()
  const [cuentas, setCuentas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [ventaDetalleId, setVentaDetalleId] = useState(null)
  const [descargandoId, setDescargandoId] = useState(null)
  const [filtroEstado, setFiltroEstado] = useFiltroPersistente(
    'cuentasPorCobrar.estado',
    'todos'
  )
  const [filtroEntrega, setFiltroEntrega] = useFiltroPersistente(
    'cuentasPorCobrar.entrega',
    'todos'
  )
  const [rangoFechas, setRangoFechas] = useFiltroPersistente('cuentasPorCobrar.fechas', {
    desde: '',
    hasta: '',
  })

  async function cargarCuentas() {
    setCargando(true)
    setError('')
    try {
      const { data } = await clienteApi.get('/ventas/cuentas-por-cobrar/')
      setCuentas(data)
    } catch {
      setError('No fue posible cargar las cuentas por cobrar.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargarCuentas()
  }, [])

  function registrarAbono(cuenta) {
    navegar(`/cartera/${cuenta.id}/abono`)
  }

  async function descargarComprobante(cuenta) {
    setError('')
    const ventana = window.open('', '_blank')
    if (!ventana) {
      setError(
        'El navegador bloqueó la ventana del comprobante. Permite las ventanas emergentes e inténtalo de nuevo.'
      )
      return
    }

    setDescargandoId(cuenta.id)
    try {
      const venta = await obtenerDetalleVenta(cuenta.venta_id)
      imprimirComprobanteVenta(venta, ventana)
    } catch (errorDescarga) {
      ventana.close()
      setError(errorDescarga.message || 'No fue posible descargar el PDF de la venta.')
    } finally {
      setDescargandoId(null)
    }
  }

  const cuentasFiltradas = cuentas.filter((cuenta) => {
    const coincideVencimiento = estaEnRangoDeFechas(
      cuenta.fecha_vencimiento,
      rangoFechas.desde,
      rangoFechas.hasta
    )
    const coincideEstado =
      filtroEstado === 'todos' || String(cuenta.estado).toLowerCase() === filtroEstado
    const estadoEntrega = cuenta.estado_entrega ?? 'pendiente_entrega'
    return (
      coincideVencimiento &&
      coincideEstado &&
      (filtroEntrega === 'todos' || estadoEntrega === filtroEntrega)
    )
  })

  function descargarReporte() {
    setError('')
    try {
      imprimirReportePdf({
        titulo: 'Cuentas por cobrar',
        descripcion: `Fecha de vencimiento: ${rangoFechas.desde || 'sin límite'} a ${rangoFechas.hasta || 'sin límite'}. Se incluyen los filtros seleccionados en el listado.`,
        columnas: [
          'Fecha venta',
          'Venta',
          'Cliente',
          'Vencimiento',
          'Total',
          'Saldo',
          'Estado',
          'Entrega',
        ],
        filas: cuentasFiltradas.map((cuenta) => [
          cuenta.fecha_venta ? formatearFechaCorta(cuenta.fecha_venta) : 'N/D',
          cuenta.numero_venta,
          cuenta.cliente,
          cuenta.fecha_vencimiento
            ? formatearFechaCorta(cuenta.fecha_vencimiento)
            : 'N/D',
          formatearPesos(Number(cuenta.total)),
          formatearPesos(Number(cuenta.saldo)),
          String(cuenta.estado).toUpperCase(),
          ETIQUETAS_ENTREGA[cuenta.estado_entrega] ?? 'Pendiente de entrega',
        ]),
      })
    } catch (errorReporte) {
      setError(errorReporte.message || 'No fue posible preparar el reporte PDF.')
    }
  }

  const totalPendiente = cuentasFiltradas.reduce(
    (total, cuenta) => total + Number(cuenta.saldo || 0),
    0
  )
  const vencidas = cuentasFiltradas.filter(
    (cuenta) => String(cuenta.estado).toUpperCase() === 'VENCIDA'
  )
  const totalVencido = vencidas.reduce((total, cuenta) => total + Number(cuenta.saldo || 0), 0)

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-titulo font-bold text-azul-950">Cuentas por cobrar</h1>
        <p className="mt-1 text-sm text-azul-400">
          Créditos pendientes de clientes por ventas realizadas.
        </p>
      </header>

      {error && <Aviso>{error}</Aviso>}

      <section className="grid gap-3 sm:grid-cols-3" aria-label="Resumen de cuentas por cobrar">
        <Resumen
          Icono={WalletIcon}
          etiqueta="Saldo pendiente"
          valor={formatearPesos(totalPendiente)}
        />
        <Resumen
          Icono={CalendarIcon}
          etiqueta="Saldo vencido"
          valor={formatearPesos(totalVencido)}
          alerta
        />
        <Resumen
          Icono={HandCoinsIcon}
          etiqueta="Ventas pendientes"
          valor={String(cuentasFiltradas.length)}
        />
      </section>

      <section className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-azul-100 p-4">
          <FiltroRangoFechas
            titulo="Filtrar por fecha de vencimiento"
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
          <select
            aria-label="Filtrar cuentas por estado"
            value={filtroEstado}
            onChange={(evento) => setFiltroEstado(evento.target.value)}
            className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
          >
            <option value="todos">Todos los estados</option>
            <option value="pendiente">Pendiente</option>
            <option value="parcial">Parcial</option>
            <option value="vencida">Vencida</option>
          </select>
          <select
            aria-label="Filtrar cuentas por entrega"
            value={filtroEntrega}
            onChange={(evento) => setFiltroEntrega(evento.target.value)}
            className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
          >
            <option value="todos">Todas las entregas</option>
            <option value="pendiente_entrega">Pendiente de entrega</option>
            <option value="entregada">Entregada</option>
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[840px] text-left text-sm">
            <thead className="bg-azul-50 text-xs uppercase text-azul-500">
              <tr>
                <th className="px-4 py-3">Fecha venta</th>
                <th className="px-4 py-3">Venta</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Vencimiento</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-right">Saldo</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Entrega</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cuentasFiltradas.map((cuenta) => (
                <tr key={cuenta.id} className="border-t border-azul-100">
                  <td className="px-4 py-3 text-xs text-azul-500">
                    {cuenta.fecha_venta ? formatearFechaCorta(cuenta.fecha_venta) : 'N/D'}
                  </td>
                  <td className="px-4 py-3 font-semibold text-azul-950">{cuenta.numero_venta}</td>
                  <td className="px-4 py-3">{cuenta.cliente}</td>
                  <td className="px-4 py-3">
                    {formatearFechaCorta(cuenta.fecha_vencimiento)}
                  </td>
                  <td className="px-4 py-3 text-right">{formatearPesos(Number(cuenta.total))}</td>
                  <td className="px-4 py-3 text-right font-bold text-azul-950">
                    {formatearPesos(Number(cuenta.saldo))}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${TONOS_ESTADO[cuenta.estado] ?? TONOS_ESTADO.PENDIENTE}`}
                    >
                      {String(cuenta.estado).toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${TONOS_ENTREGA[cuenta.estado_entrega] ?? TONOS_ENTREGA.pendiente_entrega}`}
                    >
                      {ETIQUETAS_ENTREGA[cuenta.estado_entrega] ?? 'Pendiente de entrega'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => setVentaDetalleId(cuenta.venta_id)}
                        className="rounded-lg border border-azul-200 px-3 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-50"
                      >
                        Ver detalle
                      </button>
                      <button
                        type="button"
                        onClick={() => registrarAbono(cuenta)}
                        className="rounded-lg bg-azul-950 px-3 py-1.5 text-xs font-semibold text-blanco hover:bg-azul-800"
                      >
                        Registrar abono
                      </button>
                      <button
                        type="button"
                        onClick={() => descargarComprobante(cuenta)}
                        disabled={descargandoId !== null}
                        title="Se abrirá la impresión del navegador; selecciona Guardar como PDF."
                        aria-label={`Descargar PDF de la venta ${cuenta.numero_venta}`}
                        className="inline-flex items-center gap-1 rounded-lg border border-azul-200 px-3 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <DownloadSimpleIcon size={15} />
                        {descargandoId === cuenta.id ? 'Preparando...' : 'Descargar PDF'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!cargando && !cuentasFiltradas.length && (
                <tr>
                  <td colSpan={9} className="px-4 py-10 text-center text-azul-400">
                    {cuentas.length
                      ? 'No hay cuentas que coincidan con los filtros.'
                      : 'No hay cuentas por cobrar pendientes.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {cargando && <p className="px-4 py-10 text-center text-sm text-azul-400">Cargando...</p>}
      </section>

      {ventaDetalleId && (
        <ModalDetalleVenta ventaId={ventaDetalleId} alCerrar={() => setVentaDetalleId(null)} />
      )}
    </div>
  )
}

function Resumen({ Icono, etiqueta, valor, alerta = false }) {
  return (
    <article className="rounded-xl border border-azul-150 bg-blanco p-4">
      <div className="flex items-center gap-3">
        <div
          className={`grid size-10 place-items-center rounded-lg ${alerta ? 'bg-error-50 text-error-700' : 'bg-azul-50 text-azul-700'}`}
        >
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

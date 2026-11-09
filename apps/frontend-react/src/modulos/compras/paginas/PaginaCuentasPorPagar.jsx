import { useEffect, useState } from 'react'
import { CalendarIcon, DownloadSimpleIcon, WalletIcon } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import FiltroRangoFechas from '@/componentes/ui/FiltroRangoFechas'
import { clienteApi } from '@/librerias/clienteApi'
import { estaEnRangoDeFechas } from '@/utilidades/fechas'
import { imprimirComprobanteCompra } from '@/utilidades/imprimirComprobanteCompra'
import { imprimirReportePdf } from '@/utilidades/exportarReportePdf'
import { formatearFechaCorta, formatearPesos } from '@/utilidades/formatos'
import { obtenerDetalleCompra } from '../api/apiCompras'
import ModalDetalleCompra from '../componentes/ModalDetalleCompra'

const TONOS_ESTADO = {
  PENDIENTE: 'bg-alerta-50 text-alerta-700',
  PARCIAL: 'bg-alerta-50 text-alerta-700',
  VENCIDA: 'bg-error-50 text-error-700',
}

export default function PaginaCuentasPorPagar() {
  const navegar = useNavigate()
  const [cuentas, setCuentas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [compraDetalleId, setCompraDetalleId] = useState(null)
  const [descargandoId, setDescargandoId] = useState(null)
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [rangoFechas, setRangoFechas] = useState({ desde: '', hasta: '' })

  async function cargarCuentas() {
    setCargando(true)
    setError('')
    try {
      const { data } = await clienteApi.get('/compras/cuentas-por-pagar/')
      setCuentas(data)
    } catch {
      setError('No fue posible cargar las cuentas por pagar.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargarCuentas()
  }, [])

  async function registrarAbono(cuenta) {
    navegar(`/cuentas-por-pagar/${cuenta.id}/abono`)
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
      const compra = await obtenerDetalleCompra(cuenta.compra_id)
      imprimirComprobanteCompra(compra, ventana)
    } catch (errorDescarga) {
      ventana.close()
      setError(errorDescarga.message || 'No fue posible descargar el PDF de la compra.')
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
    return (
      coincideVencimiento &&
      (filtroEstado === 'todos' || String(cuenta.estado).toLowerCase() === filtroEstado)
    )
  })
  const totalPendiente = cuentasFiltradas.reduce(
    (total, cuenta) => total + Number(cuenta.saldo || 0),
    0
  )
  const vencidas = cuentasFiltradas.filter((cuenta) => cuenta.estado === 'VENCIDA')
  const totalVencido = vencidas.reduce((total, cuenta) => total + Number(cuenta.saldo || 0), 0)

  function descargarReporte() {
    setError('')
    try {
      imprimirReportePdf({
        titulo: 'Cuentas por pagar',
        descripcion: `Fecha de vencimiento: ${rangoFechas.desde || 'sin límite'} a ${rangoFechas.hasta || 'sin límite'}. Se incluyen los filtros seleccionados en el listado.`,
        columnas: [
          'Fecha compra',
          'Compra',
          'Proveedor',
          'Vencimiento',
          'Total',
          'Saldo',
          'Estado',
        ],
        filas: cuentasFiltradas.map((cuenta) => [
          cuenta.fecha_compra ? formatearFechaCorta(new Date(cuenta.fecha_compra)) : 'N/D',
          cuenta.numero_compra,
          cuenta.proveedor,
          cuenta.fecha_vencimiento
            ? formatearFechaCorta(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))
            : 'N/D',
          formatearPesos(Number(cuenta.total)),
          formatearPesos(Number(cuenta.saldo)),
          cuenta.estado,
        ]),
      })
    } catch (errorReporte) {
      setError(errorReporte.message || 'No fue posible preparar el reporte PDF.')
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-titulo font-bold text-azul-950">Cuentas por pagar</h1>
        <p className="mt-1 text-sm text-azul-400">
          Obligaciones pendientes con proveedores por compras a crédito.
        </p>
      </header>

      {error && <Aviso>{error}</Aviso>}

      <section className="grid gap-3 sm:grid-cols-3" aria-label="Resumen de cuentas por pagar">
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
          Icono={WalletIcon}
          etiqueta="Facturas pendientes"
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
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[840px] text-left text-sm">
            <thead className="bg-azul-50 text-xs uppercase text-azul-500">
              <tr>
                <th className="px-4 py-3">Fecha compra</th>
                <th className="px-4 py-3">Compra</th>
                <th className="px-4 py-3">Proveedor</th>
                <th className="px-4 py-3">Vencimiento</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-right">Saldo</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cuentasFiltradas.map((cuenta) => (
                <tr key={cuenta.id} className="border-t border-azul-100">
                  <td className="px-4 py-3 text-xs text-azul-500">
                    {cuenta.fecha_compra
                      ? formatearFechaCorta(new Date(cuenta.fecha_compra))
                      : 'N/D'}
                  </td>
                  <td className="px-4 py-3 font-semibold text-azul-950">{cuenta.numero_compra}</td>
                  <td className="px-4 py-3">{cuenta.proveedor}</td>
                  <td className="px-4 py-3">
                    {formatearFechaCorta(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))}
                  </td>
                  <td className="px-4 py-3 text-right">{formatearPesos(Number(cuenta.total))}</td>
                  <td className="px-4 py-3 text-right font-bold text-azul-950">
                    {formatearPesos(Number(cuenta.saldo))}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${TONOS_ESTADO[cuenta.estado] ?? TONOS_ESTADO.PENDIENTE}`}
                    >
                      {cuenta.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => setCompraDetalleId(cuenta.compra_id)}
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
                        aria-label={`Descargar PDF de la compra ${cuenta.numero_compra}`}
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
                  <td colSpan={8} className="px-4 py-10 text-center text-azul-400">
                    {cuentas.length
                      ? 'No hay cuentas que coincidan con los filtros.'
                      : 'No hay cuentas por pagar pendientes.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {cargando && <p className="px-4 py-10 text-center text-sm text-azul-400">Cargando...</p>}
      </section>
      {compraDetalleId && (
        <ModalDetalleCompra compraId={compraDetalleId} alCerrar={() => setCompraDetalleId(null)} />
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

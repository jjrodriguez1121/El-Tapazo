import { useEffect, useState } from 'react'
import { CalendarIcon, HandCoinsIcon, WalletIcon } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import { clienteApi } from '@/librerias/clienteApi'
import { formatearFechaCorta, formatearPesos } from '@/utilidades/formatos'
import ModalDetalleVenta from '../componentes/ModalDetalleVenta'

const TONOS_ESTADO = {
  pendiente: 'bg-alerta-50 text-alerta-700',
  parcial: 'bg-alerta-50 text-alerta-700',
  vencida: 'bg-error-50 text-error-700',
  PENDIENTE: 'bg-alerta-50 text-alerta-700',
  PARCIAL: 'bg-alerta-50 text-alerta-700',
  VENCIDA: 'bg-error-50 text-error-700',
}

export default function PaginaCuentasPorCobrar() {
  const navegar = useNavigate()
  const [cuentas, setCuentas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [ventaDetalleId, setVentaDetalleId] = useState(null)

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

  const totalPendiente = cuentas.reduce((total, cuenta) => total + Number(cuenta.saldo || 0), 0)
  const vencidas = cuentas.filter((cuenta) => String(cuenta.estado).toUpperCase() === 'VENCIDA')
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
        <Resumen Icono={WalletIcon} etiqueta="Saldo pendiente" valor={formatearPesos(totalPendiente)} />
        <Resumen Icono={CalendarIcon} etiqueta="Saldo vencido" valor={formatearPesos(totalVencido)} alerta />
        <Resumen Icono={HandCoinsIcon} etiqueta="Ventas pendientes" valor={String(cuentas.length)} />
      </section>

      <section className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
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
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cuentas.map((cuenta) => (
                <tr key={cuenta.id} className="border-t border-azul-100">
                  <td className="px-4 py-3 text-xs text-azul-500">
                    {cuenta.fecha_venta
                      ? formatearFechaCorta(new Date(cuenta.fecha_venta))
                      : 'N/D'}
                  </td>
                  <td className="px-4 py-3 font-semibold text-azul-950">{cuenta.numero_venta}</td>
                  <td className="px-4 py-3">{cuenta.cliente}</td>
                  <td className="px-4 py-3">
                    {formatearFechaCorta(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))}
                  </td>
                  <td className="px-4 py-3 text-right">{formatearPesos(Number(cuenta.total))}</td>
                  <td className="px-4 py-3 text-right font-bold text-azul-950">
                    {formatearPesos(Number(cuenta.saldo))}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${TONOS_ESTADO[cuenta.estado] ?? TONOS_ESTADO.PENDIENTE}`}>
                      {String(cuenta.estado).toUpperCase()}
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
                    </div>
                  </td>
                </tr>
              ))}
              {!cargando && !cuentas.length && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-azul-400">
                    No hay cuentas por cobrar pendientes.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {cargando && <p className="px-4 py-10 text-center text-sm text-azul-400">Cargando...</p>}
      </section>

      {ventaDetalleId && (
        <ModalDetalleVenta
          ventaId={ventaDetalleId}
          alCerrar={() => setVentaDetalleId(null)}
        />
      )}
    </div>
  )
}

function Resumen({ Icono, etiqueta, valor, alerta = false }) {
  return (
    <article className="rounded-xl border border-azul-150 bg-blanco p-4">
      <div className="flex items-center gap-3">
        <div className={`grid size-10 place-items-center rounded-lg ${alerta ? 'bg-error-50 text-error-700' : 'bg-azul-50 text-azul-700'}`}>
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

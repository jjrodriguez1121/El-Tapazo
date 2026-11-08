import { useEffect, useState } from 'react'
import { ArrowLeftIcon, CheckCircleIcon, WalletIcon } from '@phosphor-icons/react'
import { useNavigate, useParams } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import { RUTAS } from '@/configuracion/rutas'
import { formatearFechaCorta, formatearPesos } from '@/utilidades/formatos'
import { listarMetodosPago, obtenerCuentaPorCobrar, registrarAbonoVenta } from '../api/apiVentas'

export default function PaginaRegistrarAbonoVenta() {
  const { cuentaId } = useParams()
  const navegar = useNavigate()
  const [cuenta, setCuenta] = useState(null)
  const [metodosPago, setMetodosPago] = useState([])
  const [monto, setMonto] = useState('')
  const [metodoPagoId, setMetodoPagoId] = useState('')
  const [referencia, setReferencia] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')

  async function cargar() {
    setCargando(true)
    setError('')
    try {
      const [datosCuenta, datosMetodos] = await Promise.all([
        obtenerCuentaPorCobrar(cuentaId),
        listarMetodosPago(),
      ])
      setCuenta(datosCuenta)
      setMetodosPago(datosMetodos)
      setMetodoPagoId(datosMetodos[0]?.id ? String(datosMetodos[0].id) : '')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'No fue posible cargar la cuenta por cobrar.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [cuentaId])

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setMensaje('')

    const valor = Number(monto)
    if (!Number.isFinite(valor) || valor <= 0) {
      setError('Ingresa un valor de abono mayor que cero.')
      return
    }
    if (valor > Number(cuenta.saldo)) {
      setError(`El abono no puede superar el saldo de ${formatearPesos(Number(cuenta.saldo))}.`)
      return
    }
    if (!metodoPagoId) {
      setError('Selecciona un medio de pago.')
      return
    }

    setGuardando(true)
    try {
      await registrarAbonoVenta(cuentaId, {
        monto: valor,
        metodo_pago_id: Number(metodoPagoId),
        referencia: referencia.trim(),
      })
      setMonto('')
      setReferencia('')
      setMensaje('Abono registrado correctamente.')
      await cargar()
    } catch (err) {
      const datos = err.response?.data
      setError(datos?.monto ?? datos?.detail ?? 'No fue posible registrar el abono.')
    } finally {
      setGuardando(false)
    }
  }

  const saldoActual = Number(cuenta?.saldo || 0)
  const valorAbono = Number(monto || 0)
  const nuevoSaldo = Math.max(saldoActual - (Number.isFinite(valorAbono) ? valorAbono : 0), 0)

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
      <header className="flex items-start justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={() => navegar(RUTAS.cartera)}
            className="mb-3 flex items-center gap-2 text-sm font-semibold text-azul-600 hover:text-azul-950"
          >
            <ArrowLeftIcon size={16} />
            Volver a cuentas por cobrar
          </button>
          <h1 className="text-titulo font-bold text-azul-950">Registrar abono</h1>
          <p className="mt-1 text-sm text-azul-400">
            Registra un cobro parcial o cancela el saldo total de la venta a crédito.
          </p>
        </div>
      </header>

      {error && <Aviso>{error}</Aviso>}
      {mensaje && (
        <div className="flex items-center gap-2 rounded-xl border border-verde-200 bg-verde-50 px-4 py-3 text-sm font-semibold text-verde-700">
          <CheckCircleIcon size={20} />
          {mensaje}
        </div>
      )}

      {cargando && <p className="py-10 text-center text-sm text-azul-400">Cargando cuenta...</p>}

      {!cargando && cuenta && (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <main className="flex flex-col gap-5">
            <section className="rounded-xl border border-azul-150 bg-blanco p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase text-azul-400">Venta</p>
                  <h2 className="mt-1 text-lg font-bold text-azul-950">{cuenta.numero_venta}</h2>
                  <p className="mt-1 text-sm text-azul-500">{cuenta.cliente}</p>
                </div>
                <span className="rounded-full bg-alerta-50 px-3 py-1 text-xs font-bold text-alerta-700">
                  {String(cuenta.estado).toUpperCase()}
                </span>
              </div>

              <dl className="mt-5 grid gap-4 border-t border-azul-100 pt-5 sm:grid-cols-2">
                <Dato
                  etiqueta="Fecha de venta"
                  valor={cuenta.fecha_venta ? formatearFechaCorta(new Date(cuenta.fecha_venta)) : 'N/D'}
                />
                <Dato
                  etiqueta="Fecha de vencimiento"
                  valor={formatearFechaCorta(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))}
                />
              </dl>
            </section>

            <form onSubmit={guardar} className="rounded-xl border border-azul-150 bg-blanco p-5">
              <h2 className="text-base font-bold text-azul-950">Datos del abono</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <label className="flex flex-col gap-1 text-sm font-semibold text-azul-700">
                  Valor del abono
                  <div className="flex rounded-lg border border-azul-200 bg-blanco focus-within:border-azul-600 focus-within:ring-1 focus-within:ring-azul-600">
                    <span className="grid place-items-center px-3 text-azul-400">$</span>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      max={saldoActual}
                      value={monto}
                      onChange={(evento) => setMonto(evento.target.value)}
                      placeholder="0,00"
                      required
                      className="min-w-0 flex-1 rounded-r-lg px-3 py-2.5 outline-none"
                    />
                  </div>
                </label>

                <label className="flex flex-col gap-1 text-sm font-semibold text-azul-700">
                  Medio de pago
                  <select
                    value={metodoPagoId}
                    onChange={(evento) => setMetodoPagoId(evento.target.value)}
                    required
                    className="rounded-lg border border-azul-200 px-3 py-2.5 text-sm text-azul-950 outline-none focus:border-azul-600 focus:ring-1 focus:ring-azul-600"
                  >
                    <option value="">Selecciona un medio</option>
                    {metodosPago.map((metodo) => (
                      <option key={metodo.id} value={metodo.id}>{metodo.nombre}</option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-1 text-sm font-semibold text-azul-700 sm:col-span-2">
                  Referencia (opcional)
                  <input
                    type="text"
                    value={referencia}
                    onChange={(evento) => setReferencia(evento.target.value)}
                    maxLength={100}
                    placeholder="Número de comprobante, transferencia o nota"
                    className="rounded-lg border border-azul-200 px-3 py-2.5 text-sm font-normal text-azul-950 outline-none focus:border-azul-600 focus:ring-1 focus:ring-azul-600"
                  />
                </label>
              </div>

              <div className="mt-5 flex flex-wrap gap-2 border-t border-azul-100 pt-4">
                <button
                  type="button"
                  onClick={() => setMonto(saldoActual ? String(saldoActual) : '')}
                  disabled={saldoActual <= 0}
                  className="rounded-lg border border-azul-200 px-4 py-2 text-sm font-semibold text-azul-700 hover:bg-azul-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Cobrar saldo total
                </button>
                <button
                  type="submit"
                  disabled={guardando || saldoActual <= 0 || !monto}
                  className="ml-auto rounded-lg bg-azul-950 px-5 py-2 text-sm font-semibold text-blanco hover:bg-azul-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {guardando ? 'Registrando...' : 'Registrar abono'}
                </button>
              </div>
            </form>

            <section className="rounded-xl border border-azul-150 bg-blanco p-5">
              <h2 className="text-base font-bold text-azul-950">Historial de abonos recibidos</h2>
              {cuenta.abonos?.length ? (
                <div className="mt-3 divide-y divide-azul-100">
                  {cuenta.abonos.map((abono) => (
                    <div key={abono.id} className="grid gap-2 py-3 text-sm sm:grid-cols-[1fr_1fr_auto] sm:items-center">
                      <div>
                        <p className="font-semibold text-azul-950">{abono.metodo_pago}</p>
                        <p className="text-xs text-azul-400">{abono.referencia || 'Sin referencia'}</p>
                      </div>
                      <p className="text-azul-500">
                        {new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(abono.fecha_pago))}
                      </p>
                      <p className="font-bold text-azul-950 sm:text-right">{formatearPesos(Number(abono.valor))}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-4 rounded-lg bg-azul-50 px-4 py-6 text-center text-sm text-azul-400">
                  Esta cuenta todavía no tiene abonos registrados.
                </p>
              )}
            </section>
          </main>

          <aside className="flex flex-col gap-4">
            <section className="rounded-xl bg-azul-950 p-5 text-blanco">
              <div className="flex items-center gap-3">
                <WalletIcon size={24} />
                <div>
                  <p className="text-xs text-azul-200">Saldo pendiente</p>
                  <p className="mt-1 text-2xl font-bold">{formatearPesos(saldoActual)}</p>
                </div>
              </div>
              <dl className="mt-5 space-y-3 border-t border-azul-800 pt-4 text-sm">
                <ResumenSaldo etiqueta="Total de venta" valor={formatearPesos(Number(cuenta.total))} />
                <ResumenSaldo etiqueta="Total abonado" valor={formatearPesos(Number(cuenta.abonado))} />
                <ResumenSaldo etiqueta="Nuevo saldo estimado" valor={formatearPesos(nuevoSaldo)} destacado />
              </dl>
            </section>
          </aside>
        </div>
      )}
    </div>
  )
}

function Dato({ etiqueta, valor }) {
  return (
    <div>
      <dt className="text-xs font-semibold text-azul-400">{etiqueta}</dt>
      <dd className="mt-1 font-semibold text-azul-950">{valor}</dd>
    </div>
  )
}

function ResumenSaldo({ etiqueta, valor, destacado = false }) {
  return (
    <div className={`flex justify-between gap-4 ${destacado ? 'border-t border-azul-800 pt-3 font-bold' : ''}`}>
      <dt className="text-azul-200">{etiqueta}</dt>
      <dd>{valor}</dd>
    </div>
  )
}

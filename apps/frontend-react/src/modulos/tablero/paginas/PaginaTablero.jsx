import { useEffect, useMemo, useState } from 'react'
import { CalendarIcon, TrendUpIcon, WarningIcon, WalletIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import { clienteApi } from '@/librerias/clienteApi'
import { formatearFechaLarga, formatearPesos } from '@/utilidades/formatos'

import AlertasDeStock from '../componentes/AlertasDeStock'
import GraficaDeVentasDeLaSemana from '../componentes/GraficaDeVentasDeLaSemana'
import GraficaProductosMasVendidos from '../componentes/GraficaProductosMasVendidos'
import PanelDelTablero from '../componentes/PanelDelTablero'
import TarjetaDeIndicador from '../componentes/TarjetaDeIndicador'

const APARIENCIA_DE_INDICADORES = {
  ventas: { Icono: TrendUpIcon, tono: 'exito' },
  bruta: { Icono: TrendUpIcon, tono: 'exito' },
  cobradas: { Icono: WalletIcon, tono: 'info' },
  cobrar: { Icono: WalletIcon, tono: 'alerta' },
  pagar: { Icono: WalletIcon, tono: 'error' },
  pedidos: { Icono: CalendarIcon, tono: 'alerta' },
  registradas: { Icono: CalendarIcon, tono: 'info' },
  contado: { Icono: WalletIcon, tono: 'exito' },
  credito: { Icono: WalletIcon, tono: 'alerta' },
  'stock-bajo': { Icono: WarningIcon, tono: 'error' },
}

const RESUMEN_VACIO = {
  ventas_facturadas: 0,
  ventas_netas: 0,
  utilidad_bruta: 0,
  cobrado_en_periodo: 0,
  por_cobrar: 0,
  por_pagar: 0,
  ventas_registradas: 0,
  ventas_contado: 0,
  ventas_credito: 0,
  productos_mas_vendidos: [],
  entregas_pendientes: 0,
  stock_bajo: 0,
}

function fechaLocal(valor = new Date()) {
  const anio = valor.getFullYear()
  const mes = String(valor.getMonth() + 1).padStart(2, '0')
  const dia = String(valor.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function coleccion(datos) {
  return Array.isArray(datos) ? datos : datos?.results ?? []
}

function fechaDeVenta(venta) {
  return venta.fecha_venta?.slice(0, 10) ?? ''
}

function diasDelRango(desde, hasta, ventas) {
  const totales = new Map()
  ventas.forEach((venta) => {
    const fecha = fechaDeVenta(venta)
    totales.set(fecha, (totales.get(fecha) ?? 0) + Number(venta.total || 0))
  })

  const dias = []
  const cursor = new Date(`${desde}T00:00:00`)
  const limite = new Date(`${hasta}T00:00:00`)
  while (cursor <= limite) {
    const clave = fechaLocal(cursor)
    dias.push({
      dia: new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short' }).format(cursor),
      total: totales.get(clave) ?? 0,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return dias
}

/** Resumen operativo filtrado por un rango de fechas obligatorio. */
export default function PaginaTablero() {
  const hoy = fechaLocal()
  const [desde, setDesde] = useState(hoy)
  const [hasta, setHasta] = useState(hoy)
  const [ventas, setVentas] = useState([])
  const [resumen, setResumen] = useState(RESUMEN_VACIO)
  const [alertas, setAlertas] = useState([])
  const [cuentasPorPagar, setCuentasPorPagar] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  async function cargarDashboard(rango = { desde, hasta }) {
    if (!rango.desde || !rango.hasta) {
      setError('Seleccione las dos fechas para consultar el dashboard.')
      return
    }
    if (rango.desde > rango.hasta) {
      setError('La fecha inicial no puede ser posterior a la fecha final.')
      return
    }

    setCargando(true)
    setError('')
    const [respuestaResumen, respuestaVentas, respuestaStock, respuestaCuentas] = await Promise.allSettled([
      clienteApi.get('/negocios/informes/dashboard/', { params: rango }),
      clienteApi.get('/ventas/'),
      clienteApi.get('/inventario/existencias/bajo-minimo/'),
      clienteApi.get('/compras/cuentas-por-pagar/'),
    ])

    if (respuestaResumen.status === 'fulfilled') {
      setResumen(respuestaResumen.value.data)
    } else {
      setResumen(RESUMEN_VACIO)
      setError('No fue posible cargar los indicadores del dashboard.')
    }
    if (respuestaVentas.status === 'fulfilled') {
      setVentas(coleccion(respuestaVentas.value.data))
    } else {
      setVentas([])
      setError('No fue posible cargar las ventas del periodo.')
    }
    setAlertas(respuestaStock.status === 'fulfilled' ? coleccion(respuestaStock.value.data).map((existencia) => ({
      id: existencia.id,
      producto: existencia.producto?.nombre ?? 'Producto',
      ubicacion: 'Inventario',
      disponible: Number(existencia.cantidad_disponible ?? 0),
    })) : [])
    setCuentasPorPagar(respuestaCuentas.status === 'fulfilled' ? coleccion(respuestaCuentas.value.data) : [])
    setCargando(false)
  }

  useEffect(() => {
    cargarDashboard({ desde: hoy, hasta: hoy })
  }, [])

  const ventasDelRango = useMemo(() => ventas.filter((venta) => (
    venta.estado !== 'anulada' && fechaDeVenta(venta) >= desde && fechaDeVenta(venta) <= hasta
  )), [ventas, desde, hasta])
  const totalVendido = Number(resumen.ventas_facturadas || 0)
  const dias = useMemo(() => diasDelRango(desde, hasta, ventasDelRango), [desde, hasta, ventasDelRango])
  const indicadores = [
    { id: 'ventas', etiqueta: 'Ventas facturadas', valor: formatearPesos(Number(resumen.ventas_facturadas)) },
    { id: 'bruta', etiqueta: 'Utilidad', valor: formatearPesos(Number(resumen.utilidad_bruta)) },
    { id: 'cobradas', etiqueta: 'Cobrado en el periodo', valor: formatearPesos(Number(resumen.cobrado_en_periodo)) },
    { id: 'cobrar', etiqueta: 'Por cobrar actual', valor: formatearPesos(Number(resumen.por_cobrar)) },
    { id: 'pagar', etiqueta: 'Por pagar actual', valor: formatearPesos(Number(resumen.por_pagar)) },
    { id: 'contado', etiqueta: 'Ventas de contado', valor: String(resumen.ventas_contado) },
    { id: 'credito', etiqueta: 'Ventas a crédito', valor: String(resumen.ventas_credito) },
    { id: 'pedidos', etiqueta: 'Entregas pendientes', valor: String(resumen.entregas_pendientes) },
    { id: 'stock-bajo', etiqueta: 'Stock bajo', valor: String(resumen.stock_bajo) },
    { id: 'registradas', etiqueta: 'Ventas registradas', valor: String(resumen.ventas_registradas) },
  ]

  function enviarFormulario(evento) {
    evento.preventDefault()
    cargarDashboard()
  }

  return (
    <div>
      <header className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-titulo font-semibold tracking-[-0.01em]">Dashboard</h1>
          <p className="mt-1.25 text-sm font-medium text-azul-400">Resumen del negocio para el periodo seleccionado.</p>
        </div>
        <form onSubmit={enviarFormulario} className="flex flex-wrap items-end gap-2 rounded-xl border border-azul-150 bg-blanco p-3">
          <label className="text-xs font-semibold text-azul-600">Desde
            <input required type="date" value={desde} max={hasta || undefined} onChange={(evento) => setDesde(evento.target.value)} className="mt-1 block h-9 rounded-lg border border-azul-200 px-2 text-sm text-azul-950 outline-none focus:border-azul-600" />
          </label>
          <label className="text-xs font-semibold text-azul-600">Hasta
            <input required type="date" value={hasta} min={desde || undefined} onChange={(evento) => setHasta(evento.target.value)} className="mt-1 block h-9 rounded-lg border border-azul-200 px-2 text-sm text-azul-950 outline-none focus:border-azul-600" />
          </label>
          <button type="submit" disabled={cargando} className="h-9 rounded-lg bg-azul-950 px-4 text-sm font-semibold text-blanco hover:bg-azul-800 disabled:cursor-not-allowed disabled:bg-azul-300">
            {cargando ? 'Actualizando...' : 'Aplicar filtro'}
          </button>
        </form>
      </header>

      {error && <Aviso>{error}</Aviso>}
      <p className="mb-4 text-sm font-medium text-azul-500">
        {formatearFechaLarga(new Date(`${desde}T00:00:00`))} — {formatearFechaLarga(new Date(`${hasta}T00:00:00`))}
      </p>

      <div className="mb-4.5 grid gap-3 sm:grid-cols-3 xl:grid-cols-5">
        {indicadores.map((indicador) => (
          <TarjetaDeIndicador key={indicador.id} {...APARIENCIA_DE_INDICADORES[indicador.id]} etiqueta={indicador.etiqueta} valor={indicador.valor} variacion="" compacta />
        ))}
      </div>

      <div className="grid gap-4.5 lg:grid-cols-[1.55fr_1fr]">
        <div className="flex min-w-0 flex-col gap-4.5">
          <GraficaDeVentasDeLaSemana dias={dias} total={totalVendido} titulo="Ventas por día" />
          <GraficaProductosMasVendidos productos={resumen.productos_mas_vendidos ?? []} />
        </div>
        <div className="flex min-w-0 flex-col gap-4.5">
          <AlertasDeStock alertas={alertas} />
          <PanelDelTablero titulo="Cuentas por pagar" accesorio={<WalletIcon size={20} className="text-alerta-600" />}>
            {cuentasPorPagar.length === 0 ? <p className="py-3 text-sm text-azul-400">No hay cuentas pendientes.</p> : (
              <div className="divide-y divide-azul-100">
                {cuentasPorPagar.slice(0, 5).map((cuenta) => (
                  <div key={cuenta.id} className="flex items-start justify-between gap-3 py-3 text-sm">
                    <div>
                      <p className="font-semibold text-azul-900">{cuenta.proveedor}</p>
                      <p className="text-xs text-azul-400">Vence {formatearFechaLarga(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-azul-950">{formatearPesos(Number(cuenta.saldo))}</p>
                      <p className={`text-xs font-semibold ${cuenta.estado === 'VENCIDA' ? 'text-error-600' : 'text-alerta-600'}`}>{cuenta.estado}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </PanelDelTablero>
        </div>
      </div>
    </div>
  )
}

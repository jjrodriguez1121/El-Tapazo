import { useEffect, useState } from 'react'
import { ClipboardTextIcon, PackageIcon, TrendUpIcon, WarningIcon, WalletIcon } from '@phosphor-icons/react'

import { formatearCantidad, formatearFechaLarga, formatearPesos } from '@/utilidades/formatos'

import AlertasDeStock from '../componentes/AlertasDeStock'
import GraficaDeVentasDeLaSemana from '../componentes/GraficaDeVentasDeLaSemana'
import PedidosRecientes from '../componentes/PedidosRecientes'
import ProductosMasVendidos from '../componentes/ProductosMasVendidos'
import TarjetaDeIndicador from '../componentes/TarjetaDeIndicador'
import PanelDelTablero from '../componentes/PanelDelTablero'
import { clienteApi } from '@/librerias/clienteApi'
import {
  ALERTAS_DE_STOCK,
  INDICADORES,
  PEDIDOS_RECIENTES,
  PRODUCTOS_MAS_VENDIDOS,
  VENTAS_DE_LA_SEMANA,
} from '../utilidades/datosDeEjemplo'

// Cómo se ve cada indicador. Es de la pantalla, no del dato: sigue igual cuando
// las cifras lleguen del backend.
const APARIENCIA_DE_INDICADORES = {
  ventas: { Icono: TrendUpIcon, tono: 'exito' },
  productos: { Icono: PackageIcon, tono: 'info' },
  pedidos: { Icono: ClipboardTextIcon, tono: 'alerta' },
  'stock-bajo': { Icono: WarningIcon, tono: 'error' },
}

/** Lo primero que se ve al entrar: las cifras del día y lo que pide atención. */
export default function PaginaTablero() {
  const [cuentasPorPagar, setCuentasPorPagar] = useState([])

  useEffect(() => {
    clienteApi.get('/compras/cuentas-por-pagar/')
      .then(({ data }) => setCuentasPorPagar(data))
      .catch(() => setCuentasPorPagar([]))
  }, [])

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-titulo font-semibold tracking-[-0.01em]">Dashboard</h1>
        <p className="mt-1.25 text-sm font-medium text-azul-400">
          Resumen del negocio · {formatearFechaLarga(new Date())}
        </p>
      </header>

      <div className="mb-4.5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {INDICADORES.map((indicador) => (
          <TarjetaDeIndicador
            key={indicador.id}
            {...APARIENCIA_DE_INDICADORES[indicador.id]}
            etiqueta={indicador.etiqueta}
            valor={
              indicador.esDinero
                ? formatearPesos(indicador.valor)
                : formatearCantidad(indicador.valor)
            }
            variacion={indicador.variacion}
          />
        ))}
      </div>

      <div className="grid gap-4.5 lg:grid-cols-[1.55fr_1fr]">
        <div className="flex min-w-0 flex-col gap-4.5">
          <GraficaDeVentasDeLaSemana
            dias={VENTAS_DE_LA_SEMANA.dias}
            total={VENTAS_DE_LA_SEMANA.total}
          />
          <ProductosMasVendidos productos={PRODUCTOS_MAS_VENDIDOS} />
        </div>
        <div className="flex min-w-0 flex-col gap-4.5">
          <AlertasDeStock alertas={ALERTAS_DE_STOCK} />
          <PedidosRecientes pedidos={PEDIDOS_RECIENTES} />
          <PanelDelTablero
            titulo="Cuentas por pagar"
            accesorio={<WalletIcon size={20} className="text-alerta-600" />}
          >
            {cuentasPorPagar.length === 0 ? (
              <p className="py-3 text-sm text-azul-400">No hay cuentas pendientes.</p>
            ) : (
              <div className="divide-y divide-azul-100">
                {cuentasPorPagar.map((cuenta) => (
                  <div key={cuenta.id} className="flex items-start justify-between gap-3 py-3 text-sm">
                    <div>
                      <p className="font-semibold text-azul-900">{cuenta.proveedor}</p>
                      <p className="text-xs text-azul-400">
                        Vence {formatearFechaLarga(new Date(`${cuenta.fecha_vencimiento}T00:00:00`))}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-azul-950">{formatearPesos(cuenta.saldo)}</p>
                      <p className={`text-xs font-semibold ${cuenta.estado === 'VENCIDA' ? 'text-error-600' : 'text-alerta-600'}`}>
                        {cuenta.estado}
                      </p>
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

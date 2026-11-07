import { ClipboardTextIcon, PackageIcon, TrendUpIcon, WarningIcon } from '@phosphor-icons/react'

import { formatearCantidad, formatearFechaLarga, formatearPesos } from '@/utilidades/formatos'

import AlertasDeStock from '../componentes/AlertasDeStock'
import GraficaDeVentasDeLaSemana from '../componentes/GraficaDeVentasDeLaSemana'
import PedidosRecientes from '../componentes/PedidosRecientes'
import ProductosMasVendidos from '../componentes/ProductosMasVendidos'
import TarjetaDeIndicador from '../componentes/TarjetaDeIndicador'
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
        </div>
      </div>
    </div>
  )
}

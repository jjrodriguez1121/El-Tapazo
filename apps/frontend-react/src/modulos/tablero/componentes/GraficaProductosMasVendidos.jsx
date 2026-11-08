import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'

import PanelDelTablero from './PanelDelTablero'

/** Barras horizontales: compara las unidades vendidas de los cinco productos líderes. */
export default function GraficaProductosMasVendidos({ productos }) {
  const maximo = Math.max(...productos.map((producto) => Number(producto.unidades)), 1)

  return (
    <PanelDelTablero titulo="Productos más vendidos" accesorio={<span className="text-xs font-semibold text-azul-500">Por unidades</span>}>
      {productos.length === 0 ? (
        <p className="py-4 text-sm text-azul-400">No hay productos vendidos en este periodo.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {productos.map((producto) => {
            const unidades = Number(producto.unidades)
            return (
              <li key={producto.id}>
                <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                  <span className="truncate font-semibold text-azul-900">{producto.nombre}</span>
                  <span className="shrink-0 text-xs font-semibold text-azul-500">
                    {formatearCantidad(unidades)} und · {formatearPesos(Number(producto.total))}
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-azul-100">
                  <div
                    className="h-full rounded-full bg-azul-600 transition-[width] duration-500"
                    style={{ width: `${(unidades / maximo) * 100}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </PanelDelTablero>
  )
}

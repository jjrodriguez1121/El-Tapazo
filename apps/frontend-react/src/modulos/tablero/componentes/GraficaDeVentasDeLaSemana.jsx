import { formatearPesos } from '@/utilidades/formatos'

import PanelDelTablero from './PanelDelTablero'

/** Cuánto se vendió cada día de la semana. El día más fuerte va resaltado. */
export default function GraficaDeVentasDeLaSemana({ dias, total }) {
  // Con una semana sin ventas el máximo es 0: se divide entre 1 para no pintar NaN.
  const maximo = Math.max(...dias.map((dia) => dia.total)) || 1

  return (
    <PanelDelTablero
      titulo="Ventas de la semana"
      accesorio={
        <span className="text-etiqueta font-semibold text-azul-600">{formatearPesos(total)}</span>
      }
    >
      <ul className="mt-3.5 flex items-end gap-3">
        {dias.map((dia) => (
          <li key={dia.dia} className="flex flex-1 flex-col items-center gap-2.25">
            <div className="flex h-32.5 w-full items-end">
              <div
                className={`w-full rounded-lg transition-[height] duration-500 ${dia.total === maximo ? 'bg-azul-600' : 'bg-azul-100'}`}
                style={{ height: `${(dia.total / maximo) * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-azul-400">{dia.dia}</span>
            <span className="sr-only">{formatearPesos(dia.total)}</span>
          </li>
        ))}
      </ul>
    </PanelDelTablero>
  )
}

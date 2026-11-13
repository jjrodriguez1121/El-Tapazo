import { formatearPesos } from '@/utilidades/formatos'

import PanelDelTablero from './PanelDelTablero'

/** Muestra las ventas diarias con barras uniformes y sus importes. */
export default function GraficaDeVentasDeLaSemana({ dias, total, titulo = 'Ventas de la semana' }) {
  // Con una semana sin ventas el máximo es 0: se divide entre 1 para no pintar NaN.
  const maximo = Math.max(...dias.map((dia) => dia.total)) || 1

  return (
    <PanelDelTablero
      titulo={titulo}
      accesorio={
        <span className="text-etiqueta font-semibold text-azul-600">{formatearPesos(total)}</span>
      }
    >
      <div className="mt-3.5 overflow-x-auto pb-1">
        <ul className="flex min-w-[520px] items-end gap-3">
          {dias.map((dia) => (
            <li
              key={dia.dia}
              aria-label={`${dia.dia}: ${formatearPesos(dia.total)}`}
              className="flex min-w-16 flex-1 flex-col items-center gap-2.25"
            >
              <span className="whitespace-nowrap text-[9px] font-semibold leading-3 text-azul-600">
                {formatearPesos(dia.total)}
              </span>
              <div className="flex h-32.5 w-full items-end">
                <div
                  className="w-full rounded-lg bg-azul-600 transition-[height] duration-500"
                  style={{ height: `${(dia.total / maximo) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium text-azul-400">{dia.dia}</span>
            </li>
          ))}
        </ul>
      </div>
    </PanelDelTablero>
  )
}

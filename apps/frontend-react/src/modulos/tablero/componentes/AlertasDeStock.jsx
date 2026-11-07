import { Link } from 'react-router-dom'

import Insignia from '@/componentes/ui/Insignia'
import { RUTAS } from '@/configuracion/rutas'
import { formatearCantidad } from '@/utilidades/formatos'

import PanelDelTablero from './PanelDelTablero'

/** Lo que se está acabando; lo que ya se acabó, en rojo. */
export default function AlertasDeStock({ alertas }) {
  return (
    <PanelDelTablero
      titulo="Alertas de stock"
      accesorio={<Insignia tono="error">{alertas.length} bajos</Insignia>}
    >
      {alertas.length === 0 && (
        <p className="py-4 text-etiqueta font-medium text-azul-400">Nada se está acabando.</p>
      )}

      <ul>
        {alertas.map((alerta) => {
          const agotado = alerta.disponible === 0
          return (
            <li key={alerta.id} className="flex items-center gap-3 border-b border-azul-75 py-2.75">
              <span
                aria-hidden="true"
                className={`size-2.25 flex-none rounded-full ${agotado ? 'bg-error-700' : 'bg-alerta-700'}`}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-etiqueta font-semibold">{alerta.producto}</p>
                <p className="text-xs font-medium text-azul-400">{alerta.ubicacion}</p>
              </div>
              <p
                className={`text-etiqueta font-semibold ${agotado ? 'text-error-700' : 'text-alerta-700'}`}
              >
                {formatearCantidad(alerta.disponible)} und
              </p>
            </li>
          )
        })}
      </ul>

      <Link
        to={RUTAS.productos}
        className="mt-3 block rounded-[11px] border border-azul-100 bg-azul-50 py-2.5 text-center text-etiqueta font-semibold hover:bg-azul-75 focus-visible:outline-2 focus-visible:outline-azul-300"
      >
        Ver inventario
      </Link>
    </PanelDelTablero>
  )
}

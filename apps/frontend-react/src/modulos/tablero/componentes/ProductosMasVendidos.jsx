import { ImageSquareIcon } from '@phosphor-icons/react'

import { formatearCantidad, formatearPesos } from '@/utilidades/formatos'

import PanelDelTablero from './PanelDelTablero'

/** Lo que más salió, con cuántas unidades y a qué precio. */
export default function ProductosMasVendidos({ productos }) {
  return (
    <PanelDelTablero titulo="Productos más vendidos">
      {productos.length === 0 && (
        <p className="py-4 text-etiqueta font-medium text-azul-400">Todavía no hay ventas.</p>
      )}

      <ul>
        {productos.map((producto) => (
          <li key={producto.id} className="flex items-center gap-3.5 border-b border-azul-75 py-3">
            <span
              aria-hidden="true"
              className="grid size-10.5 flex-none place-items-center rounded-[11px] rayado-de-imagen text-azul-300"
            >
              <ImageSquareIcon size={18} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{producto.nombre}</p>
              <p className="text-xs font-medium text-azul-400">
                {producto.sku} · {producto.categoria}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-azul-600">
                {formatearCantidad(producto.vendidos)} und
              </p>
              <p className="text-xs font-medium text-azul-400">{formatearPesos(producto.precio)}</p>
            </div>
          </li>
        ))}
      </ul>
    </PanelDelTablero>
  )
}

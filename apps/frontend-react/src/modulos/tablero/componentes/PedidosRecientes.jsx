import Insignia from '@/componentes/ui/Insignia'

import PanelDelTablero from './PanelDelTablero'

// Las claves son los estados de `PedidoDistribucion` en el backend.
const ESTADOS = {
  pendiente: { etiqueta: 'Pendiente', tono: 'neutro' },
  en_ruta: { etiqueta: 'En ruta', tono: 'alerta' },
  entregado: { etiqueta: 'Entregado', tono: 'exito' },
  no_entregado: { etiqueta: 'No entregado', tono: 'error' },
  cancelado: { etiqueta: 'Cancelado', tono: 'neutro' },
}

/** Los últimos pedidos mayoristas y en qué van. */
export default function PedidosRecientes({ pedidos }) {
  return (
    <PanelDelTablero titulo="Pedidos recientes">
      {pedidos.length === 0 && (
        <p className="py-4 text-etiqueta font-medium text-azul-400">Todavía no hay pedidos.</p>
      )}

      <ul>
        {pedidos.map((pedido) => {
          const estado = ESTADOS[pedido.estado]
          return (
            <li key={pedido.id} className="flex items-center gap-3 border-b border-azul-75 py-2.75">
              <div className="min-w-0 flex-1">
                <p className="truncate text-etiqueta font-semibold">
                  #{pedido.id} · {pedido.tienda}
                </p>
                <p className="text-xs font-medium text-azul-400">{pedido.detalle}</p>
              </div>
              <Insignia tono={estado.tono}>{estado.etiqueta}</Insignia>
            </li>
          )
        })}
      </ul>
    </PanelDelTablero>
  )
}

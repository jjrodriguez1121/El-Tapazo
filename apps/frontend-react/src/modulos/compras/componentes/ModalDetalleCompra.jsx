import { useEffect, useState } from 'react'
import { XIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import { formatearPesos } from '@/utilidades/formatos'
import { obtenerDetalleCompra } from '../api/apiCompras'

export default function ModalDetalleCompra({ compraId, alCerrar }) {
  const [compra, setCompra] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    obtenerDetalleCompra(compraId)
      .then(setCompra)
      .catch(() => setError('No fue posible cargar el detalle de la compra.'))
  }, [compraId])

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-azul-950/45 px-4 py-6">
      <section role="dialog" aria-modal="true" aria-labelledby="detalle-compra-titulo" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-azul-150 bg-blanco shadow-xl">
        <header className="flex items-start justify-between border-b border-azul-100 px-5 py-4">
          <div>
            <p className="text-xs font-semibold text-azul-400">Detalle de compra</p>
            <h2 id="detalle-compra-titulo" className="mt-1 text-lg font-bold text-azul-950">
              {compra?.numero_compra ?? 'Cargando...'}
            </h2>
          </div>
          <button type="button" aria-label="Cerrar detalle" onClick={alCerrar} className="grid size-9 place-items-center rounded-lg text-azul-500 hover:bg-azul-50">
            <XIcon size={18} />
          </button>
        </header>

        <div className="p-5">
          {error && <Aviso>{error}</Aviso>}
          {compra && (
            <>
              <dl className="grid gap-3 sm:grid-cols-3">
                <Dato etiqueta="Proveedor" valor={compra.proveedor_nombre} />
                <Dato etiqueta="Fecha" valor={new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(compra.fecha_compra))} />
                <Dato etiqueta="Pago" valor={compra.condicion_pago === 'CONTADO' ? 'Contado' : 'Crédito'} />
              </dl>

              <div className="mt-5 overflow-x-auto rounded-lg border border-azul-150">
                <table className="w-full min-w-[560px] text-left text-sm">
                  <thead className="bg-azul-50 text-xs uppercase text-azul-500">
                    <tr>
                      <th className="px-3 py-3">Producto</th>
                      <th className="px-3 py-3 text-right">Cantidad</th>
                      <th className="px-3 py-3 text-right">Costo</th>
                      <th className="px-3 py-3 text-right">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compra.detalles.map((detalle) => (
                      <tr key={detalle.id} className="border-t border-azul-100">
                        <td className="px-3 py-3">
                          <span className="block font-semibold text-azul-950">{detalle.producto}</span>
                          <span className="text-xs text-azul-400">{detalle.sku}</span>
                        </td>
                        <td className="px-3 py-3 text-right">{detalle.cantidad}</td>
                        <td className="px-3 py-3 text-right">{formatearPesos(Number(detalle.costo_unitario))}</td>
                        <td className="px-3 py-3 text-right font-semibold">{formatearPesos(Number(detalle.subtotal))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="ml-auto mt-4 w-full max-w-xs space-y-1 text-sm">
                <div className="flex justify-between"><span className="text-azul-500">Subtotal</span><span>{formatearPesos(Number(compra.subtotal))}</span></div>
                <div className="flex justify-between border-t border-azul-150 pt-2 text-base font-bold text-azul-950">
                  <span>Total</span><span>{formatearPesos(Number(compra.total))}</span>
                </div>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}

function Dato({ etiqueta, valor }) {
  return (
    <div className="rounded-lg border border-azul-150 bg-azul-50/40 px-3 py-2">
      <dt className="text-[11px] text-azul-400">{etiqueta}</dt>
      <dd className="mt-1 text-sm font-bold text-azul-950">{valor}</dd>
    </div>
  )
}

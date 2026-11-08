import { useEffect, useState } from 'react'
import { CheckCircleIcon, TrashIcon, XIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import ConfirmacionAccion from '@/componentes/ui/ConfirmacionAccion'
import { formatearPesos } from '@/utilidades/formatos'
import { anularVenta, confirmarEntregaVenta, obtenerDetalleVenta } from '../api/apiVentas'

export default function ModalDetalleVenta({ ventaId, alCerrar, alActualizar }) {
  const [venta, setVenta] = useState(null)
  const [error, setError] = useState('')
  const [procesando, setProcesando] = useState(false)
  const [confirmacionEntregaAbierta, setConfirmacionEntregaAbierta] = useState(false)

  useEffect(() => {
    obtenerDetalleVenta(ventaId)
      .then(setVenta)
      .catch(() => setError('No fue posible cargar el detalle de la venta.'))
  }, [ventaId])

  async function guardarEntrega() {
    setProcesando(true)
    setError('')
    try {
      await confirmarEntregaVenta(ventaId)
      const actualizada = await obtenerDetalleVenta(ventaId)
      setVenta(actualizada)
      alActualizar?.()
      setConfirmacionEntregaAbierta(false)
    } catch (errorSolicitud) {
      setError(errorSolicitud.response?.data?.[0] ?? 'No fue posible confirmar la entrega.')
      setConfirmacionEntregaAbierta(false)
    } finally {
      setProcesando(false)
    }
  }

  async function anular() {
    if (!window.confirm('¿Anular esta venta? Los productos regresarán al inventario.')) return

    setProcesando(true)
    setError('')
    try {
      await anularVenta(ventaId)
      const actualizada = await obtenerDetalleVenta(ventaId)
      setVenta(actualizada)
      alActualizar?.()
    } catch (errorSolicitud) {
      setError(errorSolicitud.response?.data?.[0] ?? 'No fue posible anular la venta.')
    } finally {
      setProcesando(false)
    }
  }

  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-azul-950/45 px-4 py-6">
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="detalle-venta-titulo"
          className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-azul-150 bg-blanco shadow-xl"
        >
          <header className="flex items-start justify-between border-b border-azul-100 px-5 py-4">
            <div>
              <p className="text-xs font-semibold text-azul-400">Detalle de venta</p>
              <h2 id="detalle-venta-titulo" className="mt-1 text-lg font-bold text-azul-950">
                {venta?.numero_venta ?? 'Cargando...'}
              </h2>
            </div>
            <button
              type="button"
              aria-label="Cerrar detalle"
              onClick={alCerrar}
              className="grid size-9 place-items-center rounded-lg text-azul-500 hover:bg-azul-50"
            >
              <XIcon size={18} />
            </button>
          </header>

          <div className="p-5">
            {error && <Aviso>{error}</Aviso>}
            {venta && (
              <>
                <dl className="grid gap-3 sm:grid-cols-3">
                  <Dato etiqueta="Cliente" valor={venta.cliente_nombre} />
                  <Dato
                    etiqueta="Fecha"
                    valor={new Intl.DateTimeFormat('es-CO', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }).format(new Date(venta.fecha_venta))}
                  />
                  <Dato
                    etiqueta="Tipo de pago"
                    valor={venta.tipo_pago === 'contado' ? 'Contado' : 'Crédito'}
                  />
                  <Dato etiqueta="Entrega" valor={etiquetaEntrega(venta.estado_entrega)} />
                </dl>

                {venta.estado_entrega === 'pendiente_entrega' && (
                  <div className="mt-4 flex flex-wrap justify-end gap-2">
                    <button
                      type="button"
                      disabled={procesando}
                      onClick={anular}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-error-200 px-3 py-2 text-xs font-bold text-error-700 hover:bg-error-50 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <TrashIcon size={16} /> Anular venta
                    </button>
                    <button
                      type="button"
                      disabled={procesando}
                      onClick={() => setConfirmacionEntregaAbierta(true)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-exito-700 px-3 py-2 text-xs font-bold text-blanco hover:bg-exito-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <CheckCircleIcon size={16} weight="bold" />
                      {procesando ? 'Guardando...' : 'Confirmar entrega'}
                    </button>
                  </div>
                )}

                <div className="mt-5 overflow-x-auto rounded-lg border border-azul-150">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead className="bg-azul-50 text-xs uppercase text-azul-500">
                      <tr>
                        <th className="px-3 py-3">Producto</th>
                        <th className="px-3 py-3 text-right">Cantidad</th>
                        <th className="px-3 py-3 text-right">Precio unitario</th>
                        <th className="px-3 py-3 text-right">Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {venta.detalles.map((detalle) => (
                        <tr key={detalle.id} className="border-t border-azul-100">
                          <td className="px-3 py-3">
                            <span className="block font-semibold text-azul-950">
                              {detalle.producto}
                            </span>
                            <span className="text-xs text-azul-400">{detalle.sku}</span>
                          </td>
                          <td className="px-3 py-3 text-right">{detalle.cantidad}</td>
                          <td className="px-3 py-3 text-right">
                            {formatearPesos(Number(detalle.precio_unitario))}
                          </td>
                          <td className="px-3 py-3 text-right font-semibold">
                            {formatearPesos(Number(detalle.subtotal))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="ml-auto mt-4 w-full max-w-xs space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-azul-500">Subtotal</span>
                    <span>{formatearPesos(Number(venta.subtotal))}</span>
                  </div>
                  {Number(venta.descuento) > 0 && (
                    <div className="flex justify-between text-azul-500">
                      <span>Descuento</span>
                      <span>- {formatearPesos(Number(venta.descuento))}</span>
                    </div>
                  )}
                  {Number(venta.total_iva) > 0 && (
                    <div className="flex justify-between text-azul-500">
                      <span>IVA</span>
                      <span>{formatearPesos(Number(venta.total_iva))}</span>
                    </div>
                  )}
                  <div className="flex justify-between border-t border-azul-150 pt-2 text-base font-bold text-azul-950">
                    <span>Total</span>
                    <span>{formatearPesos(Number(venta.total))}</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </section>
      </div>
      {confirmacionEntregaAbierta && venta && (
        <ConfirmacionAccion
          titulo="Confirmar entrega"
          descripcion={`¿Confirmas que la venta ${venta.numero_venta} ya fue entregada a ${venta.cliente_nombre}? Esta acción actualizará el estado de entrega.`}
          textoConfirmar="Confirmar entrega"
          variante="positiva"
          procesando={procesando}
          alConfirmar={guardarEntrega}
          alCancelar={() => setConfirmacionEntregaAbierta(false)}
        />
      )}
    </>
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

function etiquetaEntrega(estado) {
  return (
    {
      pendiente_entrega: 'Pendiente de entrega',
      entregada: 'Entregada',
      anulada: 'Anulada',
    }[estado] ?? 'Pendiente de entrega'
  )
}

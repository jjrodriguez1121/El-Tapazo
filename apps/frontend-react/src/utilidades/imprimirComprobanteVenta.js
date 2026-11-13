import { formatearFechaHora, formatearPesos } from './formatos.js'

function escaparHtml(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function imprimirComprobanteVenta(venta, ventana = window.open('', '_blank')) {
  if (!ventana) {
    throw new Error(
      'El navegador bloqueó la ventana del comprobante. Permite las ventanas emergentes e inténtalo de nuevo.'
    )
  }

  const fechaVenta = venta.fecha_venta
    ? formatearFechaHora(venta.fecha_venta)
    : 'No registrada'
  const detalles = (venta.detalles ?? [])
    .map(
      (detalle) => `<tr>
        <td>${escaparHtml(detalle.producto)}<small>${escaparHtml(detalle.sku)}</small></td>
        <td class="numero">${escaparHtml(detalle.cantidad)}</td>
        <td class="numero">${escaparHtml(formatearPesos(Number(detalle.precio_unitario)))}</td>
        <td class="numero">${escaparHtml(formatearPesos(Number(detalle.subtotal)))}</td>
      </tr>`
    )
    .join('')
  const estadoEntrega =
    {
      pendiente_entrega: 'Pendiente de entrega',
      entregada: 'Entregada',
      anulada: 'Anulada',
    }[venta.estado_entrega] ?? 'Pendiente de entrega'

  ventana.document.write(`<!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <title>Comprobante de venta ${escaparHtml(venta.numero_venta)}</title>
        <style>
          @page { margin: 16mm; }
          body { color: #172554; font: 13px Arial, sans-serif; }
          header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #172554; padding-bottom: 16px; }
          h1 { margin: 0 0 5px; font-size: 22px; }
          h2 { margin: 22px 0 10px; font-size: 14px; }
          p { margin: 4px 0; color: #475569; }
          .marca { font-size: 16px; font-weight: 700; }
          .numero { text-align: right; white-space: nowrap; }
          .datos { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; margin-top: 20px; }
          .datos strong { color: #172554; }
          table { width: 100%; margin-top: 16px; border-collapse: collapse; }
          th, td { padding: 9px 8px; border-bottom: 1px solid #cbd5e1; text-align: left; }
          th { background: #eff6ff; font-size: 10px; text-transform: uppercase; }
          td small { display: block; margin-top: 3px; color: #64748b; }
          .totales { width: min(100%, 300px); margin: 16px 0 0 auto; }
          .totales p { display: flex; justify-content: space-between; padding: 5px 0; }
          .total { border-top: 1px solid #94a3b8; padding-top: 10px !important; color: #172554; font-size: 16px; font-weight: 700; }
          footer { margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 10px; color: #64748b; font-size: 10px; }
          tr { break-inside: avoid; }
        </style>
      </head>
      <body>
        <header>
          <div><p class="marca">Distribuidora El Tapazo</p><p>Comprobante interno de venta</p></div>
          <div class="numero"><h1>Venta ${escaparHtml(venta.numero_venta)}</h1><p>${escaparHtml(fechaVenta)}</p></div>
        </header>
        <section class="datos">
          <p><strong>Cliente:</strong> ${escaparHtml(venta.cliente_nombre || 'Cliente general / Mostrador')}</p>
          <p><strong>Vendedor:</strong> ${escaparHtml(venta.vendedor || 'N/D')}</p>
          <p><strong>Condición de pago:</strong> ${venta.tipo_pago === 'contado' ? 'Contado' : 'Crédito'}</p>
          <p><strong>Estado de entrega:</strong> ${escaparHtml(estadoEntrega)}</p>
        </section>
        <h2>Productos vendidos</h2>
        <table>
          <thead><tr><th>Producto</th><th class="numero">Cantidad</th><th class="numero">Precio unitario</th><th class="numero">Subtotal</th></tr></thead>
          <tbody>${detalles || `<tr><td colspan="4">No hay productos registrados.</td></tr>`}</tbody>
        </table>
        <section class="totales">
          <p><span>Subtotal</span><strong>${escaparHtml(formatearPesos(Number(venta.subtotal)))}</strong></p>
          ${Number(venta.descuento) > 0 ? `<p><span>Descuento</span><strong>- ${escaparHtml(formatearPesos(Number(venta.descuento)))}</strong></p>` : ''}
          ${Number(venta.total_iva) > 0 ? `<p><span>IVA</span><strong>${escaparHtml(formatearPesos(Number(venta.total_iva)))}</strong></p>` : ''}
          <p class="total"><span>Total</span><span>${escaparHtml(formatearPesos(Number(venta.total)))}</span></p>
        </section>
        <footer>Este documento es un comprobante interno y no reemplaza una factura electrónica o documento equivalente.</footer>
        <script>window.onload = () => window.print(); window.onafterprint = () => window.close();</script>
      </body>
    </html>`)
  ventana.document.close()
}

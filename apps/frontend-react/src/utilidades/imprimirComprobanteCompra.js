import { formatearFechaCorta, formatearFechaHora, formatearPesos } from './formatos.js'

function escaparHtml(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function imprimirComprobanteCompra(compra, ventana = window.open('', '_blank')) {
  if (!ventana) {
    throw new Error(
      'El navegador bloqueó la ventana del comprobante. Permite las ventanas emergentes e inténtalo de nuevo.'
    )
  }

  const fechaCompra = compra.fecha_compra
    ? formatearFechaHora(compra.fecha_compra)
    : 'No registrada'
  const detalles = (compra.detalles ?? [])
    .map(
      (detalle) => `<tr>
        <td>${escaparHtml(detalle.producto)}<small>${escaparHtml(detalle.sku)}</small></td>
        <td class="numero">${escaparHtml(detalle.cantidad)}</td>
        <td class="numero">${escaparHtml(formatearPesos(Number(detalle.costo_unitario)))}</td>
        <td class="numero">${escaparHtml(formatearPesos(Number(detalle.subtotal)))}</td>
      </tr>`
    )
    .join('')
  const fechaVencimiento = compra.fecha_vencimiento
    ? formatearFechaCorta(compra.fecha_vencimiento)
    : 'No aplica'

  ventana.document.write(`<!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <title>Comprobante de compra ${escaparHtml(compra.numero_compra)}</title>
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
          <div><p class="marca">Distribuidora El Tapazo</p><p>Comprobante interno de compra</p></div>
          <div class="numero"><h1>Compra ${escaparHtml(compra.numero_compra)}</h1><p>${escaparHtml(fechaCompra)}</p></div>
        </header>
        <section class="datos">
          <p><strong>Proveedor:</strong> ${escaparHtml(compra.proveedor_nombre)}</p>
          <p><strong>Factura del proveedor:</strong> ${escaparHtml(compra.numero_factura || 'No registrada')}</p>
          <p><strong>Condición de pago:</strong> ${compra.condicion_pago === 'CONTADO' ? 'Contado' : 'Crédito'}</p>
          <p><strong>Vencimiento:</strong> ${escaparHtml(fechaVencimiento)}</p>
        </section>
        <h2>Productos recibidos</h2>
        <table>
          <thead><tr><th>Producto</th><th class="numero">Cantidad</th><th class="numero">Costo unitario</th><th class="numero">Subtotal</th></tr></thead>
          <tbody>${detalles || `<tr><td colspan="4">No hay productos registrados.</td></tr>`}</tbody>
        </table>
        <section class="totales">
          <p><span>Subtotal</span><strong>${escaparHtml(formatearPesos(Number(compra.subtotal)))}</strong></p>
          <p><span>Descuento</span><strong>${escaparHtml(formatearPesos(Number(compra.descuento)))}</strong></p>
          <p><span>IVA</span><strong>${escaparHtml(formatearPesos(Number(compra.total_iva)))}</strong></p>
          <p class="total"><span>Total</span><span>${escaparHtml(formatearPesos(Number(compra.total)))}</span></p>
        </section>
        <footer>Este documento es un comprobante interno y no reemplaza la factura electrónica emitida por el proveedor.</footer>
        <script>window.onload = () => window.print(); window.onafterprint = () => window.close();</script>
      </body>
    </html>`)
  ventana.document.close()
}

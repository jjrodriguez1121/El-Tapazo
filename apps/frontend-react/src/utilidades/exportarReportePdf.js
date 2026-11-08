function escaparHtml(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function imprimirReportePdf({ titulo, descripcion, columnas, filas }) {
  const ventana = window.open('', '_blank')
  if (!ventana) {
    throw new Error(
      'El navegador bloqueó la ventana del reporte. Permite las ventanas emergentes e inténtalo de nuevo.'
    )
  }

  const encabezados = columnas.map((columna) => `<th>${escaparHtml(columna)}</th>`).join('')
  const cuerpo = filas
    .map((fila) => `<tr>${fila.map((celda) => `<td>${escaparHtml(celda)}</td>`).join('')}</tr>`)
    .join('')
  const fechaGeneracion = escaparHtml(
    new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date())
  )

  ventana.document.write(`<!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <title>${escaparHtml(titulo)}</title>
        <style>
          @page { size: landscape; margin: 12mm; }
          body { color: #172554; font: 12px Arial, sans-serif; }
          h1 { margin: 0 0 6px; font-size: 20px; }
          p { margin: 0 0 18px; color: #475569; }
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 7px 8px; border: 1px solid #cbd5e1; text-align: left; }
          th { background: #eff6ff; font-size: 10px; text-transform: uppercase; }
          tr { break-inside: avoid; }
          footer { margin-top: 14px; color: #64748b; font-size: 10px; }
        </style>
      </head>
      <body>
        <h1>${escaparHtml(titulo)}</h1>
        <p>${escaparHtml(descripcion)}</p>
        <table>
          <thead><tr>${encabezados}</tr></thead>
          <tbody>${cuerpo || `<tr><td colspan="${columnas.length}">No hay registros para los filtros seleccionados.</td></tr>`}</tbody>
        </table>
        <footer>Generado el ${fechaGeneracion} · Distribuidora El Tapazo</footer>
        <script>window.onload = () => window.print(); window.onafterprint = () => window.close();</script>
      </body>
    </html>`)
  ventana.document.close()
}

import { afterEach, describe, expect, test, vi } from 'vitest'

import { imprimirReportePdf } from './exportarReportePdf'

describe('imprimirReportePdf', () => {
  afterEach(() => vi.restoreAllMocks())

  test('genera un reporte escapando valores para que no se interpreten como HTML', () => {
    const documento = { write: vi.fn(), close: vi.fn() }
    vi.spyOn(window, 'open').mockReturnValue({ document: documento })

    imprimirReportePdf({
      titulo: 'Ventas <hoy>',
      descripcion: 'Reporte & detalle',
      columnas: ['Cliente'],
      filas: [['<script>alert(1)</script>']],
    })

    const html = documento.write.mock.calls[0][0]
    expect(html).toContain('Ventas &lt;hoy&gt;')
    expect(html).toContain('Reporte &amp; detalle')
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;')
    expect(documento.close).toHaveBeenCalledOnce()
  })

  test('informa si el navegador bloquea la ventana del reporte', () => {
    vi.spyOn(window, 'open').mockReturnValue(null)

    expect(() =>
      imprimirReportePdf({ titulo: 'Reporte', descripcion: '', columnas: [], filas: [] })
    ).toThrow('El navegador bloqueó la ventana del reporte.')
  })
})

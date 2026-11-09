import { afterEach, describe, expect, test, vi } from 'vitest'

import { imprimirComprobanteVenta } from './imprimirComprobanteVenta'

describe('imprimirComprobanteVenta', () => {
  afterEach(() => vi.restoreAllMocks())

  test('incluye los datos de venta y escapa los valores del cliente y productos', () => {
    const documento = { write: vi.fn(), close: vi.fn() }
    vi.spyOn(window, 'open').mockReturnValue({ document: documento })

    imprimirComprobanteVenta({
      numero_venta: 'VEN-0025',
      cliente_nombre: 'Cliente & Asociados',
      vendedor: 'Ana <Cajera>',
      fecha_venta: '2026-11-08T15:00:00Z',
      tipo_pago: 'contado',
      estado_entrega: 'entregada',
      subtotal: '10084.03',
      descuento: '600',
      total_iva: '1915.97',
      total: '12000',
      detalles: [
        {
          producto: '<Bujía>',
          sku: 'ELC-003',
          cantidad: '1.00',
          precio_unitario: '12000',
          subtotal: '12000',
        },
      ],
    })

    const html = documento.write.mock.calls[0][0]
    expect(html).toContain('Venta VEN-0025')
    expect(html).toContain('Cliente &amp; Asociados')
    expect(html).toContain('Ana &lt;Cajera&gt;')
    expect(html).toContain('&lt;Bujía&gt;')
    expect(html).toContain('Este documento es un comprobante interno')
    expect(documento.close).toHaveBeenCalledOnce()
  })

  test('informa si el navegador bloquea la ventana de impresión', () => {
    vi.spyOn(window, 'open').mockReturnValue(null)

    expect(() => imprimirComprobanteVenta({})).toThrow(
      'El navegador bloqueó la ventana del comprobante.'
    )
  })

  test('usa una ventana abierta previamente', () => {
    const documento = { write: vi.fn(), close: vi.fn() }
    const ventana = { document }
    const abrirVentana = vi.spyOn(window, 'open')

    imprimirComprobanteVenta({}, ventana)

    expect(abrirVentana).not.toHaveBeenCalled()
    expect(documento.close).toHaveBeenCalledOnce()
  })
})

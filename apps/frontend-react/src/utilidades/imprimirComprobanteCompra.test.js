import { afterEach, describe, expect, test, vi } from 'vitest'

import { imprimirComprobanteCompra } from './imprimirComprobanteCompra'

describe('imprimirComprobanteCompra', () => {
  afterEach(() => vi.restoreAllMocks())

  test('incluye datos de compra y escapa los valores del proveedor y productos', () => {
    const documento = { write: vi.fn(), close: vi.fn() }
    vi.spyOn(window, 'open').mockReturnValue({ document: documento })

    imprimirComprobanteCompra({
      numero_compra: 'C-001',
      numero_factura: '<F-123>',
      proveedor_nombre: 'Proveedor & Asociados',
      condicion_pago: 'CREDITO',
      fecha_vencimiento: '2026-12-01',
      subtotal: '10000',
      descuento: '500',
      total_iva: '1900',
      total: '10000',
      detalles: [
        {
          producto: '<Gaseosa>',
          sku: 'SKU-1',
          cantidad: 2,
          costo_unitario: '5000',
          subtotal: '10000',
        },
      ],
    })

    const html = documento.write.mock.calls[0][0]
    expect(html).toContain('Compra C-001')
    expect(html).toContain('&lt;F-123&gt;')
    expect(html).toContain('Proveedor &amp; Asociados')
    expect(html).toContain('&lt;Gaseosa&gt;')
    expect(html).toContain('Este documento es un comprobante interno')
    expect(documento.close).toHaveBeenCalledOnce()
  })

  test('informa si el navegador bloquea la ventana de impresión', () => {
    vi.spyOn(window, 'open').mockReturnValue(null)

    expect(() => imprimirComprobanteCompra({})).toThrow(
      'El navegador bloqueó la ventana del comprobante.'
    )
  })
})

import { clienteApi } from '@/librerias/clienteApi'

export async function listarCompras() {
  const { data } = await clienteApi.get('/compras/')
  return data
}

export async function crearCompra(datos) {
  const { data } = await clienteApi.post('/compras/', datos)
  return data
}

export async function obtenerDetalleCompra(compraId) {
  const { data } = await clienteApi.get(`/compras/${compraId}/`)
  return data
}

export async function registrarAbonoCompra(cuentaId, datos) {
  const { data } = await clienteApi.post(`/compras/cuentas-por-pagar/${cuentaId}/abonos/`, datos)
  return data
}

export async function obtenerCuentaPorPagar(cuentaId) {
  const { data } = await clienteApi.get(`/compras/cuentas-por-pagar/${cuentaId}/`)
  return data
}

/** Sube una factura de proveedor en PDF y devuelve sus renglones cruzados con el catálogo. */
export async function buscarCoincidenciasFacturaPdf(archivo) {
  const formulario = new FormData()
  formulario.append('archivo', archivo)
  const { data } = await clienteApi.post('/compras/facturas-pdf/coincidencias/', formulario, {
    timeout: 60000,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

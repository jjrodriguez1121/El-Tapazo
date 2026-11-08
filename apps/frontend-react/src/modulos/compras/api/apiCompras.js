import { clienteApi } from '@/librerias/clienteApi'

export async function listarCompras() {
  const { data } = await clienteApi.get('/compras/')
  return data
}

export async function crearCompra(datos) {
  const { data } = await clienteApi.post('/compras/', datos)
  return data
}

export async function registrarAbonoCompra(cuentaId, datos) {
  const { data } = await clienteApi.post(`/compras/cuentas-por-pagar/${cuentaId}/abonos/`, datos)
  return data
}

import { clienteApi } from '@/librerias/clienteApi'

export async function crearVenta(datos) {
  const { data } = await clienteApi.post('/ventas/', datos)
  return data
}

export async function listarMetodosPago() {
  const { data } = await clienteApi.get('/ventas/metodos-pago/')
  return data
}

export async function registrarAbonoVenta(cuentaId, datos) {
  const { data } = await clienteApi.post(`/ventas/cuentas-por-cobrar/${cuentaId}/abonos/`, datos)
  return data
}

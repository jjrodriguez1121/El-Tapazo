import { clienteApi } from '@/librerias/clienteApi'

export async function listarPqrs({ page = 1, ambito, search } = {}) {
  const { data } = await clienteApi.get('/pqrs/', {
    params: {
      page,
      ...(ambito && { ambito }),
      ...(search && { search }),
    },
  })
  return data
}

export async function obtenerResumenPqrs() {
  const { data } = await clienteApi.get('/pqrs/resumen/')
  return data
}

export async function crearPqr(datos) {
  const { data } = await clienteApi.post('/pqrs/', datos)
  return data
}

export async function registrarSeguimientoPqr(pqrId, datos) {
  const { data } = await clienteApi.post(`/pqrs/${pqrId}/seguimientos/`, datos)
  return data
}

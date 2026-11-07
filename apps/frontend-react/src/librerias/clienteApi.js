import axios from 'axios'

import { entorno } from '@/configuracion/entorno'
import { RUTAS } from '@/configuracion/rutas'
import { borrarSesion, guardarTokens, leerRefresco, leerTokenDeAcceso } from '@/estado/sesion'

/** Cliente HTTP compartido. Los módulos lo usan desde su carpeta `api/`. */
export const clienteApi = axios.create({
  baseURL: entorno.urlApi,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

clienteApi.interceptors.request.use((configuracion) => {
  const token = leerTokenDeAcceso()
  if (token) configuracion.headers.Authorization = `Bearer ${token}`
  return configuracion
})

// Una sola renovación a la vez. El backend rota el refresco: si dos peticiones
// fallan juntas y cada una renovara por su cuenta, la segunda usaría un refresco
// ya anulado y sacaría a la persona de la aplicación.
let renovacionEnCurso = null

function renovarSesion() {
  renovacionEnCurso ??= axios
    .post(`${entorno.urlApi}/usuarios/sesiones/renovacion/`, { refresco: leerRefresco() })
    .then(({ data }) => {
      guardarTokens({ tokenDeAcceso: data.acceso, tokenDeRefresco: data.refresco })
      return data.acceso
    })
    .finally(() => {
      renovacionEnCurso = null
    })
  return renovacionEnCurso
}

// Solo se renueva cuando caducó el acceso, y una sola vez por petición. Con
// `credenciales_invalidas` o `sesion_invalida` no: renovar no los arregla.
async function reintentarConLaSesionRenovada(error) {
  const peticion = error.config
  const codigo = error.response?.data?.error?.codigo
  if (codigo !== 'no_autenticado' || peticion._reintentada || !leerRefresco()) {
    return Promise.reject(error)
  }

  peticion._reintentada = true
  try {
    peticion.headers.Authorization = `Bearer ${await renovarSesion()}`
  } catch {
    borrarSesion()
    window.location.assign(RUTAS.acceso)
    return Promise.reject(error)
  }
  return clienteApi(peticion)
}

clienteApi.interceptors.response.use((respuesta) => respuesta, reintentarConLaSesionRenovada)

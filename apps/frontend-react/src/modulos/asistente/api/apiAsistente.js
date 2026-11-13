import { clienteApi } from '@/librerias/clienteApi'

// La IA puede tardar bastante más que el resto de la API.
const TIEMPO_LIMITE_IA_MS = 90000

/** `mensajes`: [{ rol: 'usuario' | 'asistente', contenido }]. Devuelve el texto de la respuesta. */
export async function conversarConAsistente(mensajes) {
  const { data } = await clienteApi.post(
    '/asistente/chat/',
    { mensajes },
    { timeout: TIEMPO_LIMITE_IA_MS }
  )
  return data.respuesta
}

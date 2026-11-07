import { useSyncExternalStore } from 'react'

/*
 * La sesión: quién entró y con qué tokens.
 *
 * Es estado de interfaz, no datos del servidor, por eso vive aquí y no en React
 * Query. El refresco va en localStorage para que la sesión sobreviva a un F5; el
 * acceso, solo en memoria, porque es el que viaja en cada petición y el que
 * menos dura. Ver docs/guias/guia-api-autenticacion.md §2.
 */

const CLAVE_DEL_REFRESCO = 'el-tapaso:refresco'

let tokenDeAcceso = null
let usuario = null
const oyentes = new Set()

function avisarDelCambio() {
  oyentes.forEach((oyente) => oyente())
}

function suscribirse(oyente) {
  oyentes.add(oyente)
  return () => oyentes.delete(oyente)
}

export const leerTokenDeAcceso = () => tokenDeAcceso

export function leerRefresco() {
  try {
    return localStorage.getItem(CLAVE_DEL_REFRESCO)
  } catch {
    // Navegador en modo privado o almacenamiento bloqueado: no hay refresco.
    return null
  }
}

export function guardarTokens({ tokenDeAcceso: acceso, tokenDeRefresco }) {
  tokenDeAcceso = acceso
  try {
    localStorage.setItem(CLAVE_DEL_REFRESCO, tokenDeRefresco)
  } catch {
    // Sin almacenamiento la sesión dura lo que dure la pestaña.
  }
}

/** Guarda una sesión recién abierta: los dos tokens y quién entró. */
export function guardarSesion({ tokenDeAcceso: acceso, tokenDeRefresco, usuario: quienEntro }) {
  guardarTokens({ tokenDeAcceso: acceso, tokenDeRefresco })
  usuario = quienEntro
  avisarDelCambio()
}

export function guardarUsuario(quienEntro) {
  usuario = quienEntro
  avisarDelCambio()
}

export function borrarSesion() {
  tokenDeAcceso = null
  usuario = null
  try {
    localStorage.removeItem(CLAVE_DEL_REFRESCO)
  } catch {
    // Si no se pudo leer, tampoco hay nada que borrar.
  }
  avisarDelCambio()
}

/** El usuario con la sesión abierta, o `null`. Vuelve a pintar cuando cambia. */
export function useUsuarioDeSesion() {
  return useSyncExternalStore(suscribirse, () => usuario)
}

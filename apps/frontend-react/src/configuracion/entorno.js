/** Único punto donde se leen las variables de entorno de Vite. */
export const entorno = {
  urlApi: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  nombreApp: import.meta.env.VITE_APP_NAME ?? 'El Tapaso',
  esDesarrollo: import.meta.env.DEV,
}

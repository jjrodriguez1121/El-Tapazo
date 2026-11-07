import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { clienteConsultas } from '@/librerias/clienteConsultas'

/** Envuelve la app con los proveedores globales (datos, rutas, tema, sesión...). */
export default function Proveedores({ children }) {
  return (
    <QueryClientProvider client={clienteConsultas}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

function RutaActual() {
  const { pathname } = useLocation()
  return <p>Ahora en {pathname}</p>
}

/**
 * Monta una pantalla en `ruta` con lo que necesita para vivir: un cliente de
 * consultas propio (sin reintentos, para que un error se vea al instante) y un
 * router. Si la pantalla navega a otra ruta, se pinta «Ahora en /esa-ruta».
 */
export function renderizarEnRuta(pantalla, ruta = '/') {
  const clienteConsultas = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const [camino] = ruta.split('?')

  return render(
    <QueryClientProvider client={clienteConsultas}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path={camino} element={pantalla} />
          <Route path="*" element={<RutaActual />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

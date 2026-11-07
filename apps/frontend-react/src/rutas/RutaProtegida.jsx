import { Navigate } from 'react-router-dom'

import EsqueletoDePlantillaPrincipal from '@/componentes/estructura/EsqueletoDePlantillaPrincipal'
import { RUTAS } from '@/configuracion/rutas'
import { useSesion } from '@/modulos/autenticacion/hooks/useSesion'
import EsqueletoDelTablero from '@/modulos/tablero/componentes/EsqueletoDelTablero'

/**
 * Deja pasar solo con la sesión abierta. Esconder una pantalla no es seguridad:
 * el backend vuelve a comprobar el token en cada petición. Esto es comodidad.
 */
export default function RutaProtegida({ children }) {
  const { usuario, cargando } = useSesion()

  if (cargando) {
    return (
      <EsqueletoDePlantillaPrincipal>
        <EsqueletoDelTablero />
      </EsqueletoDePlantillaPrincipal>
    )
  }

  if (!usuario) return <Navigate to={RUTAS.acceso} replace />

  return children
}

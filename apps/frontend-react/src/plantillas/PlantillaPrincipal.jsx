import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'

import Encabezado from '@/componentes/estructura/Encabezado'
import MenuLateral from '@/componentes/estructura/MenuLateral'
import RecordatorioDePausa from '@/componentes/estructura/RecordatorioDePausa'
import { useUsuarioDeSesion } from '@/estado/sesion'
import { useCerrarSesion } from '@/modulos/autenticacion/hooks/useCerrarSesion'

// Temporalmente un minuto para validar el recordatorio. Al terminar las pruebas,
// quitar la prop `intervaloMs` del componente para recuperar sus 60 minutos.
const INTERVALO_DE_PAUSA_EN_PRUEBA_MS = 60 * 1000

/**
 * El armazón del panel para quien ya entró: el menú lateral, la barra de arriba
 * y la pantalla abierta.
 *
 * En escritorio el menú está siempre a la vista. En el celular vive escondido a
 * la izquierda: se abre con el botón de la barra y se cierra al elegir una
 * sección, al tocar fuera o con Esc.
 */
export default function PlantillaPrincipal() {
  const usuario = useUsuarioDeSesion()
  const cierre = useCerrarSesion()
  const [menuAbierto, setMenuAbierto] = useState(false)

  // Escuchar el teclado del documento es sincronizar con algo de fuera de React.
  useEffect(() => {
    if (!menuAbierto) return undefined
    const cerrarConEsc = (evento) => {
      if (evento.key === 'Escape') setMenuAbierto(false)
    }
    document.addEventListener('keydown', cerrarConEsc)
    return () => document.removeEventListener('keydown', cerrarConEsc)
  }, [menuAbierto])

  // Al salir, la sesión se borra un instante antes de navegar al acceso.
  if (!usuario) return null

  const cerrarMenu = () => setMenuAbierto(false)

  return (
    <div className="flex min-h-dvh bg-azul-50 text-azul-950">
      {menuAbierto && (
        <button
          type="button"
          aria-label="Cerrar el menú"
          onClick={cerrarMenu}
          className="fixed inset-0 z-30 bg-azul-950/40 lg:hidden"
        />
      )}

      {/* `invisible` saca el menú cerrado del orden de tabulación en el celular. */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-62 flex-none transition-[translate,visibility] lg:visible lg:sticky lg:top-0 lg:h-dvh lg:translate-x-0 ${menuAbierto ? 'visible translate-x-0' : 'invisible -translate-x-full'}`}
      >
        <MenuLateral
          usuario={usuario}
          alNavegar={cerrarMenu}
          alCerrarSesion={() => cierre.mutate()}
          cerrandoSesion={cierre.isPending}
        />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <Encabezado
          usuario={usuario}
          menuAbierto={menuAbierto}
          alAbrirMenu={() => setMenuAbierto(true)}
        />
        <main className="flex-1 px-4 py-6 sm:px-8 sm:py-7">
          <Outlet />
        </main>
      </div>
      <RecordatorioDePausa intervaloMs={INTERVALO_DE_PAUSA_EN_PRUEBA_MS} />
    </div>
  )
}

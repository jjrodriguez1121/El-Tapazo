import { ListIcon } from '@phosphor-icons/react'

import CintaInformativa from './CintaInformativa'
import UsuarioEnSesion from './UsuarioEnSesion'

const CLASES_DE_BOTON_CUADRADO =
  'grid size-10.5 flex-none place-items-center rounded-xl border border-azul-100 bg-blanco text-azul-600 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-300'

/** La barra de arriba: abrir el menú en el celular y mostrar quién está dentro. */
export default function Encabezado({ usuario, menuAbierto, alAbrirMenu }) {
  return (
    <header className="flex h-18.5 flex-none items-center gap-3 border-b border-azul-100 bg-blanco px-4 sm:px-7">
      <button
        type="button"
        onClick={alAbrirMenu}
        aria-label="Abrir el menú"
        aria-expanded={menuAbierto}
        className={`${CLASES_DE_BOTON_CUADRADO} lg:hidden`}
      >
        <ListIcon size={20} aria-hidden="true" />
      </button>

      <CintaInformativa />

      <div className="ml-auto flex items-center gap-3">
        <UsuarioEnSesion usuario={usuario} />
      </div>
    </header>
  )
}

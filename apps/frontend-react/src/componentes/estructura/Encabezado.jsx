import { BellIcon, ListIcon, PlusIcon } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

import { RUTAS } from '@/configuracion/rutas'

import CintaInformativa from './CintaInformativa'
import UsuarioEnSesion from './UsuarioEnSesion'

const CLASES_DE_BOTON_CUADRADO =
  'grid size-10.5 flex-none place-items-center rounded-xl border border-azul-100 bg-blanco text-azul-600 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-300'

/** La barra de arriba: abrir el menú en el celular, vender, los avisos y quién está dentro. */
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
        <Link
          to={RUTAS.puntoDeVenta}
          className="flex items-center gap-2 rounded-xl bg-azul-950 px-3 py-2.75 text-sm font-semibold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-300 sm:px-4.5"
        >
          <PlusIcon size={17} aria-hidden="true" />
          <span className="sr-only sm:not-sr-only">Nueva venta</span>
        </Link>

        <button type="button" aria-label="Avisos" className={CLASES_DE_BOTON_CUADRADO}>
          <BellIcon size={19} aria-hidden="true" />
        </button>

        <UsuarioEnSesion usuario={usuario} />
      </div>
    </header>
  )
}

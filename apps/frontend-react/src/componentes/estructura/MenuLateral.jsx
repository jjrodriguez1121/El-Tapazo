import { SignOutIcon } from '@phosphor-icons/react'

import { CONFIGURACION_DEL_MENU, puedeVerElemento, seccionesVisibles } from '@/configuracion/menu'

import ElementoDelMenu from './ElementoDelMenu'
import { CLASES_DE_FILA_DEL_MENU, CLASES_DE_FILA_INACTIVA } from './estilosDelMenu'
import MarcaDelNegocio from './MarcaDelNegocio'

/** El menú lateral: el negocio, las secciones que le tocan a quien entró y la salida. */
export default function MenuLateral({ usuario, alNavegar, alCerrarSesion, cerrandoSesion }) {
  return (
    <nav
      aria-label="Menú principal"
      className="flex h-full flex-col overflow-y-auto bg-azul-950 px-4 py-5.5"
    >
      <MarcaDelNegocio negocio={usuario.negocio} />

      {seccionesVisibles(usuario.esAdministrador).map((seccion) => (
        <div key={seccion.titulo} className="mb-4">
          <p className="px-2.5 pb-2 text-antetitulo font-semibold tracking-[0.12em] text-azul-400 uppercase">
            {seccion.titulo}
          </p>
          <ul className="flex flex-col gap-0.5">
            {seccion.elementos.map((elemento) => (
              <li key={elemento.ruta}>
                <ElementoDelMenu elemento={elemento} alNavegar={alNavegar} />
              </li>
            ))}
          </ul>
        </div>
      ))}

      <div className="mt-auto flex flex-col gap-0.5 border-t border-blanco/7 pt-3.5">
        {puedeVerElemento(CONFIGURACION_DEL_MENU, usuario.esAdministrador) && (
          <ElementoDelMenu elemento={CONFIGURACION_DEL_MENU} alNavegar={alNavegar} />
        )}
        <button
          type="button"
          onClick={alCerrarSesion}
          disabled={cerrandoSesion}
          className={`${CLASES_DE_FILA_DEL_MENU} ${CLASES_DE_FILA_INACTIVA} disabled:cursor-progress`}
        >
          <SignOutIcon size={19} aria-hidden="true" />
          {cerrandoSesion ? 'Saliendo…' : 'Salir'}
        </button>
      </div>
    </nav>
  )
}

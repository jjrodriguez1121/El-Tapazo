import { NavLink } from 'react-router-dom'

import {
  CLASES_DE_FILA_ACTIVA,
  CLASES_DE_FILA_DEL_MENU,
  CLASES_DE_FILA_INACTIVA,
} from './estilosDelMenu'

/** Un enlace del menú lateral. El de la pantalla abierta se resalta y su ícono se rellena. */
export default function ElementoDelMenu({ elemento, alNavegar }) {
  const { ruta, etiqueta, Icono } = elemento

  return (
    <NavLink
      to={ruta}
      onClick={alNavegar}
      className={({ isActive }) =>
        `${CLASES_DE_FILA_DEL_MENU} ${isActive ? CLASES_DE_FILA_ACTIVA : CLASES_DE_FILA_INACTIVA}`
      }
    >
      {({ isActive }) => (
        <>
          <Icono size={19} weight={isActive ? 'fill' : 'regular'} aria-hidden="true" />
          <span className="flex-1">{etiqueta}</span>
        </>
      )}
    </NavLink>
  )
}

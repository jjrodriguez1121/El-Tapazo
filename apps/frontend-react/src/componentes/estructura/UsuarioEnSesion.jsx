import { NOMBRES_DE_ROL } from '@/configuracion/roles'
import { iniciales } from '@/utilidades/iniciales'

/**
 * Quién tiene la sesión abierta. En un bar el mismo teléfono pasa de mano en
 * mano: tiene que verse de un vistazo. En el celular solo cabe la inicial; el
 * nombre sigue ahí para el lector de pantalla.
 */
export default function UsuarioEnSesion({ usuario }) {
  const rol = NOMBRES_DE_ROL[usuario.rol] ?? 'Staff de la plataforma'

  return (
    <div className="flex items-center gap-2.5 pl-1.5">
      <span
        aria-hidden="true"
        className="grid size-10 flex-none place-items-center rounded-full bg-linear-135 from-azul-600 to-azul-950 text-sm font-semibold text-blanco"
      >
        {iniciales(usuario.nombreCompleto)}
      </span>
      <div className="sr-only leading-tight sm:not-sr-only">
        <p className="text-sm font-semibold">{usuario.nombreCompleto}</p>
        <p className="text-xs font-medium text-azul-400">{rol}</p>
      </div>
    </div>
  )
}

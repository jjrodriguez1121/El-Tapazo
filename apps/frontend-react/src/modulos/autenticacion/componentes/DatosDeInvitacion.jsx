import { NOMBRES_DE_ROL } from '@/configuracion/roles'

function Dato({ nombre, children }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="font-semibold text-azul-400">{nombre}</dt>
      <dd className="min-w-0 truncate font-bold">{children}</dd>
    </div>
  )
}

/**
 * El correo, el negocio y el rol de la invitación. Se enseñan como datos y no
 * como campos: los decidió quien invitó y no se pueden cambiar.
 */
export default function DatosDeInvitacion({ invitacion }) {
  return (
    <dl className="flex flex-col gap-2.5 rounded-2xl border border-azul-150 bg-azul-50 px-4.5 py-4 text-etiqueta">
      <Dato nombre="Correo">{invitacion.correo}</Dato>
      <Dato nombre="Negocio">{invitacion.negocio}</Dato>
      <Dato nombre="Rol">
        <span className="rounded-full bg-azul-950 px-2.5 py-0.75 text-xs font-bold text-blanco">
          {NOMBRES_DE_ROL[invitacion.rol] ?? invitacion.rol}
        </span>
      </Dato>
    </dl>
  )
}

import { useSearchParams } from 'react-router-dom'

import EsqueletoDeAcceso from '../componentes/EsqueletoDeAcceso'
import FormularioDeInvitacion from '../componentes/FormularioDeInvitacion'
import InvitacionNoDisponible from '../componentes/InvitacionNoDisponible'
import { useInvitacionPendiente } from '../hooks/useInvitacionPendiente'

/**
 * La primera pantalla de todo trabajador nuevo. Llega desde el enlace del correo
 * (`?token=…`): primero enseña de qué es la invitación, después pide los datos.
 */
export default function PaginaAceptarInvitacion() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token') ?? ''
  const invitacion = useInvitacionPendiente(token)

  if (!token) return <InvitacionNoDisponible />

  if (invitacion.isPending) {
    return <EsqueletoDeAcceso campos={4} conCaja mensaje="Buscando tu invitación…" />
  }

  if (invitacion.isError) {
    return (
      <InvitacionNoDisponible error={invitacion.error} alReintentar={() => invitacion.refetch()} />
    )
  }

  return <FormularioDeInvitacion token={token} invitacion={invitacion.data} />
}

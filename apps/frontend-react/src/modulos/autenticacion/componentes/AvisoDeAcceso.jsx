import Aviso from '@/componentes/ui/Aviso'
import { codigoDeError, esErrorDeConexion, mensajeDeError } from '@/utilidades/errores'

import { useSolicitarVerificacion } from '../hooks/useSolicitarVerificacion'

/**
 * Por qué no se pudo entrar. El texto es el que manda el backend; lo que decide
 * este componente, según el `codigo`, es qué salida ofrecer.
 */
export default function AvisoDeAcceso({ error, correo, alReintentar }) {
  const reenvio = useSolicitarVerificacion()

  if (reenvio.isSuccess) {
    return <Aviso tono="exito">Te reenviamos el enlace. Revisa tu bandeja de entrada.</Aviso>
  }
  if (reenvio.isError) return <Aviso>{mensajeDeError(reenvio.error)}</Aviso>

  if (esErrorDeConexion(error)) {
    return (
      <Aviso textoDeAccion="Volver a intentar" alPulsarAccion={alReintentar}>
        {mensajeDeError(error)}
      </Aviso>
    )
  }

  if (codigoDeError(error) === 'correo_no_verificado') {
    return (
      <Aviso
        textoDeAccion={reenvio.isPending ? 'Reenviando…' : 'Reenviar el enlace'}
        alPulsarAccion={reenvio.isPending ? undefined : () => reenvio.mutate(correo)}
      >
        {mensajeDeError(error)}
      </Aviso>
    )
  }

  return <Aviso>{mensajeDeError(error)}</Aviso>
}

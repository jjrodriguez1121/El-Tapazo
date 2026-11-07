import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'
import { RUTAS } from '@/configuracion/rutas'

import { useSolicitarVerificacion } from '../hooks/useSolicitarVerificacion'
import EncabezadoDeAcceso from './EncabezadoDeAcceso'
import FormularioDeCorreo from './FormularioDeCorreo'
import TarjetaDeResultado from './TarjetaDeResultado'

/** Pedir otro enlace de verificación, cuando el anterior venció o nunca llegó. */
export default function ReenvioDeVerificacion() {
  const solicitud = useSolicitarVerificacion()

  if (solicitud.isSuccess) {
    return (
      <TarjetaDeResultado
        tono="exito"
        titulo="Revisa tu bandeja."
        acciones={<EnlacePrincipal a={RUTAS.acceso}>Volver a iniciar sesión</EnlacePrincipal>}
      >
        Si ese correo está registrado y le falta la verificación, te llegó un enlace nuevo.
      </TarjetaDeResultado>
    )
  }

  return (
    <>
      <EncabezadoDeAcceso antetitulo="Verificar correo" titulo="Pide otro enlace">
        Escribe tu correo y te enviamos otro enlace de verificación.
      </EncabezadoDeAcceso>
      <FormularioDeCorreo
        textoDelBoton="Reenviar el enlace"
        enviando={solicitud.isPending}
        error={solicitud.error}
        alEnviar={solicitud.mutate}
      />
    </>
  )
}

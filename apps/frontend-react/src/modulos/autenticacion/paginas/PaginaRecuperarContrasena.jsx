import BotonDeTexto from '@/componentes/ui/BotonDeTexto'
import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'
import { RUTAS } from '@/configuracion/rutas'

import EncabezadoDeAcceso from '../componentes/EncabezadoDeAcceso'
import FormularioDeCorreo from '../componentes/FormularioDeCorreo'
import TarjetaDeResultado from '../componentes/TarjetaDeResultado'
import { useSolicitarRecuperacion } from '../hooks/useSolicitarRecuperacion'

/**
 * «Olvidé mi contraseña». Después de enviar, la respuesta es siempre la misma,
 * exista o no el correo: si cambiara, serviría para averiguar quién tiene cuenta.
 */
export default function PaginaRecuperarContrasena() {
  const solicitud = useSolicitarRecuperacion()

  if (solicitud.isSuccess) {
    return (
      <TarjetaDeResultado
        tono="exito"
        titulo="Revisa tu bandeja."
        acciones={
          <>
            <EnlacePrincipal a={RUTAS.acceso}>Volver a iniciar sesión</EnlacePrincipal>
            <BotonDeTexto onClick={() => solicitud.reset()}>Enviarlo a otro correo</BotonDeTexto>
          </>
        }
      >
        Si ese correo está registrado, te llegó un enlace para poner una contraseña nueva.
      </TarjetaDeResultado>
    )
  }

  return (
    <>
      <EncabezadoDeAcceso antetitulo="Recuperar acceso" titulo="Recupera tu contraseña">
        Escribe tu correo y te enviamos un enlace para cambiarla.
      </EncabezadoDeAcceso>
      <FormularioDeCorreo
        textoDelBoton="Enviarme el enlace"
        enviando={solicitud.isPending}
        error={solicitud.error}
        alEnviar={solicitud.mutate}
      />
    </>
  )
}

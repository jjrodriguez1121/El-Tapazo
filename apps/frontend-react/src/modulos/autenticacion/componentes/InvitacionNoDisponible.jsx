import Boton from '@/componentes/ui/Boton'
import EnlaceDeTexto from '@/componentes/ui/EnlaceDeTexto'
import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'
import { RUTAS } from '@/configuracion/rutas'
import { codigoDeError, esErrorDeConexion, mensajeDeError } from '@/utilidades/errores'

import TarjetaDeResultado from './TarjetaDeResultado'

const TARJETAS = {
  invitacion_no_encontrada: {
    titulo: 'Esa invitación no existe.',
    texto:
      'Revisa que hayas abierto el enlace completo del correo. Si sigue igual, pídele al administrador de tu negocio que te envíe otro.',
  },
  invitacion_vencida: {
    titulo: 'La invitación venció.',
    texto: 'Pídele al administrador de tu negocio que te envíe otra.',
  },
  invitacion_ya_aceptada: {
    titulo: 'Esa invitación ya se usó.',
    texto: 'Tu cuenta ya está creada. Inicia sesión con tu correo y la contraseña que definiste.',
  },
}

/**
 * Por qué no hay invitación que aceptar. Sin `error` es que el enlace llegó sin
 * token, y para quien lo abre eso es lo mismo que una invitación que no existe.
 */
export default function InvitacionNoDisponible({ error, alReintentar }) {
  if (esErrorDeConexion(error)) {
    return (
      <TarjetaDeResultado
        tono="error"
        titulo="No pudimos cargar tu invitación."
        acciones={<Boton onClick={alReintentar}>Volver a intentar</Boton>}
      >
        {mensajeDeError(error)}
      </TarjetaDeResultado>
    )
  }

  const codigo = error ? codigoDeError(error) : 'invitacion_no_encontrada'
  const tarjeta = TARJETAS[codigo] ?? {
    titulo: 'No pudimos cargar tu invitación.',
    texto: mensajeDeError(error),
  }
  const yaSeUso = codigo === 'invitacion_ya_aceptada'

  return (
    <TarjetaDeResultado
      tono="error"
      titulo={tarjeta.titulo}
      acciones={
        <>
          <EnlacePrincipal a={RUTAS.acceso}>
            {yaSeUso ? 'Iniciar sesión' : 'Ir a iniciar sesión'}
          </EnlacePrincipal>
          {yaSeUso && (
            <EnlaceDeTexto a={RUTAS.recuperarContrasena}>Olvidé mi contraseña</EnlaceDeTexto>
          )}
        </>
      }
    >
      {tarjeta.texto}
    </TarjetaDeResultado>
  )
}

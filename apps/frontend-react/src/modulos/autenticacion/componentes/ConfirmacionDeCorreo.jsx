import Boton from '@/componentes/ui/Boton'
import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'
import { RUTAS } from '@/configuracion/rutas'
import { codigoDeError, mensajeDeError } from '@/utilidades/errores'

import { useConfirmarVerificacion } from '../hooks/useConfirmarVerificacion'
import ComprobandoEnlace from './ComprobandoEnlace'
import TarjetaDeEnlaceInvalido from './TarjetaDeEnlaceInvalido'
import TarjetaDeResultado from './TarjetaDeResultado'

/** Confirma el correo con el enlace apenas se abre, y cuenta cómo salió. */
export default function ConfirmacionDeCorreo({ enlace, alPedirOtroEnlace }) {
  const confirmacion = useConfirmarVerificacion(enlace)

  if (confirmacion.isPending) return <ComprobandoEnlace />

  if (codigoDeError(confirmacion.error) === 'enlace_invalido') {
    return (
      <TarjetaDeEnlaceInvalido
        acciones={<Boton onClick={alPedirOtroEnlace}>Pedir otro enlace</Boton>}
      />
    )
  }

  if (confirmacion.isError) {
    return (
      <TarjetaDeResultado
        tono="error"
        titulo="No pudimos comprobar el enlace."
        acciones={<Boton onClick={() => confirmacion.refetch()}>Volver a intentar</Boton>}
      >
        {mensajeDeError(confirmacion.error)}
      </TarjetaDeResultado>
    )
  }

  return (
    <TarjetaDeResultado
      tono="exito"
      titulo="Tu correo quedó verificado."
      acciones={<EnlacePrincipal a={RUTAS.acceso}>Iniciar sesión</EnlacePrincipal>}
    >
      Ya puedes entrar al sistema con tu correo y tu contraseña.
    </TarjetaDeResultado>
  )
}

import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import Aviso from '@/componentes/ui/Aviso'
import Boton from '@/componentes/ui/Boton'
import CampoContrasena from '@/componentes/ui/CampoContrasena'
import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'
import { RUTAS } from '@/configuracion/rutas'
import { codigoDeError, mensajeDeError } from '@/utilidades/errores'

import EncabezadoDeAcceso from '../componentes/EncabezadoDeAcceso'
import ReglasDeContrasena from '../componentes/ReglasDeContrasena'
import TarjetaDeEnlaceInvalido from '../componentes/TarjetaDeEnlaceInvalido'
import TarjetaDeResultado from '../componentes/TarjetaDeResultado'
import { enlaceDesdeParametros, enlaceEstaCompleto } from '../dtos/enlace'
import { useRestablecerContrasena } from '../hooks/useRestablecerContrasena'
import { contrasenaEsValida, LARGO_MAXIMO_DE_CONTRASENA } from '../utilidades/reglasDeContrasena'

/** Llega desde el enlace de recuperación (`?uid=…&token=…`) y pide la contraseña nueva. */
export default function PaginaNuevaContrasena() {
  const [parametros] = useSearchParams()
  const enlace = enlaceDesdeParametros(parametros)
  const [contrasena, setContrasena] = useState('')
  const [intentoRechazado, setIntentoRechazado] = useState(false)
  const restablecimiento = useRestablecerContrasena()
  const codigo = codigoDeError(restablecimiento.error)

  function alEnviar(evento) {
    evento.preventDefault()
    const valida = contrasenaEsValida(contrasena)
    setIntentoRechazado(!valida)
    if (valida) restablecimiento.mutate({ ...enlace, contrasena })
  }

  if (!enlaceEstaCompleto(enlace) || codigo === 'enlace_invalido') {
    return (
      <TarjetaDeEnlaceInvalido
        acciones={
          <EnlacePrincipal a={RUTAS.recuperarContrasena}>Pedir un enlace nuevo</EnlacePrincipal>
        }
      />
    )
  }

  if (restablecimiento.isSuccess) {
    return (
      <TarjetaDeResultado
        tono="exito"
        titulo="Tu contraseña quedó lista."
        acciones={<EnlacePrincipal a={RUTAS.acceso}>Iniciar sesión</EnlacePrincipal>}
      >
        Ya puedes entrar con tu correo y la contraseña nueva.
      </TarjetaDeResultado>
    )
  }

  const rechazada =
    (intentoRechazado && !contrasenaEsValida(contrasena)) || codigo === 'contrasena_insegura'

  return (
    <>
      <EncabezadoDeAcceso antetitulo="Recuperar acceso" titulo="Pon tu contraseña nueva">
        Es la que vas a usar para entrar desde ahora.
      </EncabezadoDeAcceso>

      {restablecimiento.isError && codigo !== 'contrasena_insegura' && (
        <Aviso>{mensajeDeError(restablecimiento.error)}</Aviso>
      )}

      <form onSubmit={alEnviar} noValidate className="flex flex-col gap-6.5">
        <div className="flex flex-col gap-2.5">
          <CampoContrasena
            etiqueta="Tu contraseña nueva"
            autoComplete="new-password"
            maxLength={LARGO_MAXIMO_DE_CONTRASENA}
            placeholder="••••••"
            value={contrasena}
            onChange={(evento) => setContrasena(evento.target.value)}
            invalido={rechazada}
          />
          <ReglasDeContrasena contrasena={contrasena} rechazada={rechazada} />
        </div>

        <Boton type="submit" cargando={restablecimiento.isPending}>
          {restablecimiento.isPending ? 'Guardando…' : 'Guardar la contraseña'}
        </Boton>
      </form>
    </>
  )
}

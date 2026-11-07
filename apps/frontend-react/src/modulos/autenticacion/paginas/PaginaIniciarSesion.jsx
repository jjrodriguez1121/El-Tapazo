import { useState } from 'react'

import Boton from '@/componentes/ui/Boton'
import CampoContrasena from '@/componentes/ui/CampoContrasena'
import CampoTexto from '@/componentes/ui/CampoTexto'
import EnlaceDeTexto from '@/componentes/ui/EnlaceDeTexto'
import { RUTAS } from '@/configuracion/rutas'
import { codigoDeError } from '@/utilidades/errores'

import AvisoDeAcceso from '../componentes/AvisoDeAcceso'
import EncabezadoDeAcceso from '../componentes/EncabezadoDeAcceso'
import { useIniciarSesion } from '../hooks/useIniciarSesion'
import { LARGO_MAXIMO_DE_CONTRASENA } from '../utilidades/reglasDeContrasena'
import {
  LARGO_MAXIMO_DE_CORREO,
  validarCorreo,
  validarObligatorio,
} from '../utilidades/validaciones'

/**
 * La puerta de entrada: correo y contraseña. No hay «regístrate», y no es un
 * olvido: las cuentas nacen de una invitación.
 */
export default function PaginaIniciarSesion() {
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [errores, setErrores] = useState({})
  const acceso = useIniciarSesion()

  function entrar() {
    acceso.mutate({ correo, contrasena })
  }

  function alEnviar(evento) {
    evento.preventDefault()
    const nuevosErrores = {
      correo: validarCorreo(correo),
      contrasena: validarObligatorio(contrasena, 'Escribe tu contraseña.'),
    }
    setErrores(nuevosErrores)
    if (!nuevosErrores.correo && !nuevosErrores.contrasena) entrar()
  }

  // El mensaje no dice cuál de los dos falló, a propósito: se marcan los dos.
  const credencialesInvalidas = codigoDeError(acceso.error) === 'credenciales_invalidas'

  return (
    <>
      <EncabezadoDeAcceso antetitulo="Acceso al sistema" titulo="Entra a tu negocio">
        Usa el correo con el que te invitaron.
      </EncabezadoDeAcceso>

      {acceso.isError && (
        <AvisoDeAcceso error={acceso.error} correo={correo} alReintentar={entrar} />
      )}

      <form onSubmit={alEnviar} noValidate className="flex flex-col gap-6.5">
        <div className="flex flex-col gap-4">
          <CampoTexto
            etiqueta="Correo"
            type="email"
            autoComplete="email"
            maxLength={LARGO_MAXIMO_DE_CORREO}
            placeholder="tu@correo.com"
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
            error={errores.correo}
            invalido={credencialesInvalidas}
          />
          <CampoContrasena
            etiqueta="Contraseña"
            autoComplete="current-password"
            maxLength={LARGO_MAXIMO_DE_CONTRASENA}
            placeholder="••••••"
            value={contrasena}
            onChange={(evento) => setContrasena(evento.target.value)}
            error={errores.contrasena}
            invalido={credencialesInvalidas}
          />
        </div>

        <div className="flex flex-col gap-4">
          <Boton type="submit" cargando={acceso.isPending}>
            {acceso.isPending ? 'Entrando…' : 'Entrar'}
          </Boton>
          <div className="flex flex-col items-center gap-4.5">
            <EnlaceDeTexto a={RUTAS.recuperarContrasena}>Olvidé mi contraseña</EnlaceDeTexto>
            <p className="text-center text-etiqueta leading-relaxed font-medium text-pretty text-azul-400">
              ¿No tienes cuenta? Pídele una invitación al administrador de tu negocio.
            </p>
          </div>
        </div>
      </form>
    </>
  )
}

import { useState } from 'react'

import Aviso from '@/componentes/ui/Aviso'
import Boton from '@/componentes/ui/Boton'
import CampoTexto from '@/componentes/ui/CampoTexto'
import EnlaceDeTexto from '@/componentes/ui/EnlaceDeTexto'
import { RUTAS } from '@/configuracion/rutas'
import { mensajeDeError } from '@/utilidades/errores'

import { LARGO_MAXIMO_DE_CORREO, validarCorreo } from '../utilidades/validaciones'

/**
 * Un correo y un botón: lo que piden «recuperar la contraseña» y «reenviar la
 * verificación». Quien lo usa decide qué hacer con el correo en `alEnviar`.
 */
export default function FormularioDeCorreo({ textoDelBoton, enviando, error, alEnviar }) {
  const [correo, setCorreo] = useState('')
  const [errorDelCorreo, setErrorDelCorreo] = useState('')

  function enviar(evento) {
    evento.preventDefault()
    const nuevoError = validarCorreo(correo)
    setErrorDelCorreo(nuevoError)
    if (!nuevoError) alEnviar(correo)
  }

  return (
    <>
      {error && <Aviso>{mensajeDeError(error)}</Aviso>}

      <form onSubmit={enviar} noValidate className="flex flex-col gap-6.5">
        <CampoTexto
          etiqueta="Correo"
          type="email"
          autoComplete="email"
          maxLength={LARGO_MAXIMO_DE_CORREO}
          placeholder="tu@correo.com"
          value={correo}
          onChange={(evento) => setCorreo(evento.target.value)}
          error={errorDelCorreo}
        />

        <div className="flex flex-col gap-4">
          <Boton type="submit" cargando={enviando}>
            {enviando ? 'Enviando…' : textoDelBoton}
          </Boton>
          <EnlaceDeTexto a={RUTAS.acceso}>Volver a iniciar sesión</EnlaceDeTexto>
        </div>
      </form>
    </>
  )
}

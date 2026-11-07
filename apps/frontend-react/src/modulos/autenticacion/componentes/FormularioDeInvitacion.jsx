import { useState } from 'react'

import Aviso from '@/componentes/ui/Aviso'
import Boton from '@/componentes/ui/Boton'
import CampoContrasena from '@/componentes/ui/CampoContrasena'
import CampoTexto from '@/componentes/ui/CampoTexto'
import { codigoDeError, erroresDeCampo, mensajeDeError } from '@/utilidades/errores'

import { useAceptarInvitacion } from '../hooks/useAceptarInvitacion'
import { contrasenaEsValida, LARGO_MAXIMO_DE_CONTRASENA } from '../utilidades/reglasDeContrasena'
import { validarObligatorio } from '../utilidades/validaciones'
import DatosDeInvitacion from './DatosDeInvitacion'
import EncabezadoDeAcceso from './EncabezadoDeAcceso'
import InvitacionNoDisponible from './InvitacionNoDisponible'
import ReglasDeContrasena from './ReglasDeContrasena'

// Si la invitación venció o se usó mientras la persona llenaba el formulario, ya
// no hay nada que corregir: se enseña por qué, igual que al abrir el enlace.
const CODIGOS_SIN_INVITACION = [
  'invitacion_no_encontrada',
  'invitacion_vencida',
  'invitacion_ya_aceptada',
]

// Estos se explican dentro del propio formulario, campo por campo.
const CODIGOS_DEL_FORMULARIO = ['contrasena_insegura', 'datos_invalidos']

/** Los datos de la persona y su contraseña, para crear la cuenta desde la invitación. */
export default function FormularioDeInvitacion({ token, invitacion }) {
  const [datos, setDatos] = useState({ nombre: '', apellido: '', telefono: '', contrasena: '' })
  const [errores, setErrores] = useState({})
  const [intentoRechazado, setIntentoRechazado] = useState(false)
  const aceptacion = useAceptarInvitacion()
  const codigo = codigoDeError(aceptacion.error)

  if (CODIGOS_SIN_INVITACION.includes(codigo)) {
    return <InvitacionNoDisponible error={aceptacion.error} />
  }

  const cambiar = (campo) => (evento) => {
    const valor = evento.target.value
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))
  }

  function alEnviar(evento) {
    evento.preventDefault()
    const nuevosErrores = {
      nombre: validarObligatorio(datos.nombre, 'Escribe tu nombre.'),
      apellido: validarObligatorio(datos.apellido, 'Escribe tu apellido.'),
    }
    const contrasenaValida = contrasenaEsValida(datos.contrasena)
    setErrores(nuevosErrores)
    setIntentoRechazado(!contrasenaValida)
    if (nuevosErrores.nombre || nuevosErrores.apellido || !contrasenaValida) return
    aceptacion.mutate({ token, ...datos })
  }

  const deLaApi = erroresDeCampo(aceptacion.error)
  const contrasenaRechazada =
    (intentoRechazado && !contrasenaEsValida(datos.contrasena)) || codigo === 'contrasena_insegura'

  return (
    <>
      <EncabezadoDeAcceso antetitulo="Invitación" titulo={`Te invitaron a ${invitacion.negocio}`}>
        Completa tus datos y elige tu contraseña para activar la cuenta.
      </EncabezadoDeAcceso>

      <DatosDeInvitacion invitacion={invitacion} />

      {aceptacion.isError && !CODIGOS_DEL_FORMULARIO.includes(codigo) && (
        <Aviso>{mensajeDeError(aceptacion.error)}</Aviso>
      )}

      <form onSubmit={alEnviar} noValidate className="flex flex-col gap-6.5">
        <div className="flex flex-col gap-4">
          <div className="flex gap-3">
            <CampoTexto
              etiqueta="Nombre"
              autoComplete="given-name"
              maxLength={120}
              placeholder="Daniela"
              value={datos.nombre}
              onChange={cambiar('nombre')}
              error={errores.nombre || deLaApi.nombre?.[0]}
            />
            <CampoTexto
              etiqueta="Apellido"
              autoComplete="family-name"
              maxLength={120}
              placeholder="Ruiz"
              value={datos.apellido}
              onChange={cambiar('apellido')}
              error={errores.apellido || deLaApi.apellido?.[0]}
            />
          </div>

          <CampoTexto
            etiqueta="Teléfono"
            opcional
            type="tel"
            autoComplete="tel"
            maxLength={20}
            placeholder="300 000 0000"
            value={datos.telefono}
            onChange={cambiar('telefono')}
            error={deLaApi.telefono?.[0]}
          />

          <div className="flex flex-col gap-2.5">
            <CampoContrasena
              etiqueta="Tu contraseña nueva"
              autoComplete="new-password"
              maxLength={LARGO_MAXIMO_DE_CONTRASENA}
              placeholder="••••••"
              value={datos.contrasena}
              onChange={cambiar('contrasena')}
              invalido={contrasenaRechazada}
            />
            <ReglasDeContrasena contrasena={datos.contrasena} rechazada={contrasenaRechazada} />
          </div>
        </div>

        <Boton type="submit" cargando={aceptacion.isPending}>
          {aceptacion.isPending ? 'Creando tu cuenta…' : 'Crear mi cuenta'}
        </Boton>
      </form>
    </>
  )
}

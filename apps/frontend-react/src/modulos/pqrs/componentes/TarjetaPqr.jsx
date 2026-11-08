import { useState } from 'react'
import { ClockIcon, UserIcon } from '@phosphor-icons/react'

import { mensajeDeError } from '@/utilidades/errores'
import { formatearFechaCorta } from '@/utilidades/formatos'

const ESTILOS_TIPO = {
  queja: 'bg-error-50 text-error-700 border-error-200',
  reclamo: 'bg-alerta-50 text-alerta-700 border-alerta-200',
  peticion: 'bg-azul-50 text-azul-800 border-azul-200',
  sugerencia: 'bg-exito-50 text-exito-700 border-exito-200',
}

const ESTILOS_ESTADO = {
  radicada: 'bg-alerta-50 text-alerta-700',
  en_revision: 'bg-azul-50 text-azul-800',
  en_gestion: 'bg-azul-50 text-azul-800',
  respondida: 'bg-exito-50 text-exito-700',
  cerrada: 'bg-azul-100 text-azul-800',
  no_procedente: 'bg-error-50 text-error-700',
}

const ESTADOS = [
  ['radicada', 'Radicada'],
  ['en_revision', 'En revisión'],
  ['en_gestion', 'En gestión'],
  ['respondida', 'Respondida'],
  ['cerrada', 'Cerrada'],
  ['no_procedente', 'No procedente'],
]

const TIPOS_SEGUIMIENTO = [
  ['nota', 'Nota interna'],
  ['respuesta', 'Responder al solicitante'],
  ['cambio_estado', 'Cambiar estado'],
  ['asignacion', 'Asignarme la solicitud'],
]

const ETIQUETAS_SEGUIMIENTO = {
  radicacion: 'Radicación',
  nota: 'Nota interna',
  respuesta: 'Respuesta al solicitante',
  cambio_estado: 'Cambio de estado',
  asignacion: 'Asignación',
}

export default function TarjetaPqr({ pqr, alAgregarSeguimiento }) {
  const [tipoSeguimiento, setTipoSeguimiento] = useState('nota')
  const [contenido, setContenido] = useState('')
  const [nuevoEstado, setNuevoEstado] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const esServicio = pqr.ambito === 'servicio'

  async function guardarSeguimiento(evento) {
    evento.preventDefault()
    setEnviando(true)
    setError('')
    try {
      await alAgregarSeguimiento(pqr.id, {
        tipo: tipoSeguimiento,
        contenido,
        ...(tipoSeguimiento === 'cambio_estado' && { nuevo_estado: nuevoEstado }),
      })
      setContenido('')
      setNuevoEstado('')
      setTipoSeguimiento('nota')
    } catch (errorDeGuardado) {
      setError(mensajeDeError(errorDeGuardado))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <article className="flex flex-col justify-between rounded-2xl border border-azul-150 bg-blanco p-5 shadow-[0_2px_8px_rgba(17,40,83,0.03)] transition-all hover:border-azul-200 hover:shadow-md">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-azul-150/70 pb-3">
          <div className="flex items-center gap-1.5">
            <span
              className={`rounded-lg border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider ${ESTILOS_TIPO[pqr.tipo]}`}
            >
              {pqr.tipo}
            </span>
            <span className="rounded-lg bg-azul-50 px-2 py-0.5 text-[11px] font-bold text-azul-950">
              {esServicio ? '🚚 Servicio' : '📦 Productos'}
            </span>
          </div>
          <span
            className={`rounded-lg px-2 py-0.5 text-[11px] font-bold ${ESTILOS_ESTADO[pqr.estado]}`}
          >
            {ESTADOS.find(([valor]) => valor === pqr.estado)?.[1] ?? pqr.estado}
          </span>
        </div>

        <h3 className="mt-3 text-sm font-bold leading-snug text-azul-950">{pqr.asunto}</h3>
        <p className="mt-1.5 line-clamp-3 text-xs text-azul-400">{pqr.descripcion}</p>

        <div className="mt-3.5 flex items-center gap-1.5 rounded-xl bg-azul-50 p-2.5 text-xs font-medium text-azul-950">
          <UserIcon size={14} weight="bold" className="shrink-0 text-azul-600" />
          <span className="truncate">
            <strong>Solicitante:</strong> {pqr.nombre_solicitante}
            {pqr.telefono_solicitante && ` · ${pqr.telefono_solicitante}`}
          </span>
        </div>
        {pqr.responsable_nombre && (
          <p className="mt-2 text-xs text-azul-500">
            Responsable: <strong>{pqr.responsable_nombre}</strong>
          </p>
        )}

        {pqr.seguimientos?.length > 0 && (
          <details className="mt-3 rounded-xl border border-azul-100 p-3">
            <summary className="cursor-pointer text-xs font-bold text-azul-800">
              Historial ({pqr.seguimientos.length})
            </summary>
            <ol className="mt-3 flex flex-col gap-3">
              {pqr.seguimientos.map((seguimiento) => (
                <li key={seguimiento.id} className="border-l-2 border-azul-200 pl-3">
                  <p className="text-[11px] font-bold text-azul-800">
                    {ETIQUETAS_SEGUIMIENTO[seguimiento.tipo] ?? seguimiento.tipo}
                    {seguimiento.estado_nuevo &&
                      ` · ${ESTADOS.find(([valor]) => valor === seguimiento.estado_nuevo)?.[1] ?? seguimiento.estado_nuevo}`}
                  </p>
                  {seguimiento.contenido && (
                    <p className="mt-1 whitespace-pre-wrap text-xs text-azul-600">
                      {seguimiento.contenido}
                    </p>
                  )}
                  <p className="mt-1 text-[10px] text-azul-400">
                    {seguimiento.usuario_nombre} · {formatearFechaCorta(seguimiento.creado_en)}
                  </p>
                </li>
              ))}
            </ol>
          </details>
        )}

        <form onSubmit={guardarSeguimiento} className="mt-4 border-t border-azul-100 pt-3">
          <label className="block text-xs font-bold text-azul-800" htmlFor={`pqr-accion-${pqr.id}`}>
            Registrar gestión
          </label>
          <select
            id={`pqr-accion-${pqr.id}`}
            value={tipoSeguimiento}
            onChange={(evento) => setTipoSeguimiento(evento.target.value)}
            className="mt-1.5 h-9 w-full rounded-lg border border-azul-200 bg-blanco px-2 text-xs text-azul-900"
          >
            {TIPOS_SEGUIMIENTO.map(([valor, etiqueta]) => (
              <option key={valor} value={valor}>
                {etiqueta}
              </option>
            ))}
          </select>

          {tipoSeguimiento === 'cambio_estado' && (
            <label className="mt-2 block text-xs text-azul-700">
              Nuevo estado
              <select
                required
                value={nuevoEstado}
                onChange={(evento) => setNuevoEstado(evento.target.value)}
                className="mt-1 h-9 w-full rounded-lg border border-azul-200 bg-blanco px-2 text-xs"
              >
                <option value="">Selecciona un estado</option>
                {ESTADOS.map(([valor, etiqueta]) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </label>
          )}

          {tipoSeguimiento !== 'asignacion' && (
            <textarea
              value={contenido}
              onChange={(evento) => setContenido(evento.target.value)}
              required={tipoSeguimiento === 'nota' || tipoSeguimiento === 'respuesta'}
              rows={2}
              aria-label={
                tipoSeguimiento === 'respuesta' ? 'Respuesta al solicitante' : 'Detalle de gestión'
              }
              placeholder={
                tipoSeguimiento === 'respuesta'
                  ? 'Escribe la respuesta para el solicitante...'
                  : 'Añade un detalle de la gestión...'
              }
              className="mt-2 w-full resize-y rounded-lg border border-azul-200 bg-blanco p-2 text-xs text-azul-900"
            />
          )}
          {error && (
            <p role="alert" className="mt-2 text-xs text-error-700">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={enviando}
            className="mt-2 rounded-lg bg-azul-950 px-3 py-2 text-xs font-bold text-blanco disabled:opacity-50"
          >
            {enviando ? 'Guardando...' : 'Guardar gestión'}
          </button>
        </form>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-azul-150/70 pt-2.5 text-[11px] text-azul-400">
        <span className="font-mono font-semibold text-azul-600">{pqr.radicado}</span>
        <span className="flex items-center gap-1">
          <ClockIcon size={13} />
          {formatearFechaCorta(pqr.fecha_radicacion)}
        </span>
      </div>
    </article>
  )
}

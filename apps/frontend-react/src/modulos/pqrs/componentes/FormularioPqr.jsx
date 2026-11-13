import { useState } from 'react'
import { BroomIcon, CheckCircleIcon, PaperPlaneRightIcon, UserIcon } from '@phosphor-icons/react'

import { AMBITOS_PQR, CANALES_RECEPCION, TIPOS_PQR } from '../utilidades/opcionesPqrs'
import { erroresDeCampo, mensajeDeError } from '@/utilidades/errores'
import { validarCorreoOpcional, validarTelefono } from '@/utilidades/validaciones'

/**
 * Formulario para radicar PQRs generadas a solicitud de un cliente
 * enfocado estrictamente en motivos de Servicio o Productos.
 */
export default function FormularioPqr({ alRadicar, alLimpiarExito, radicadoExitoso }) {
  const [nombreCliente, setNombreCliente] = useState('')
  const [documentoCliente, setDocumentoCliente] = useState('')
  const [telefonoCliente, setTelefonoCliente] = useState('')
  const [correoCliente, setCorreoCliente] = useState('')
  const [tipo, setTipo] = useState('queja')
  const [ambito, setAmbito] = useState('servicio')
  const [asunto, setAsunto] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [canal, setCanal] = useState('telefonico')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [erroresCampos, setErroresCampos] = useState({})

  function cambiarCampo(setter, campo) {
    return (evento) => {
      setter(evento.target.value)
      setErroresCampos((actuales) => {
        const siguientes = { ...actuales }
        delete siguientes[campo]
        return siguientes
      })
    }
  }

  function limpiarFormulario() {
    setNombreCliente('')
    setDocumentoCliente('')
    setTelefonoCliente('')
    setCorreoCliente('')
    setTipo('queja')
    setAmbito('servicio')
    setAsunto('')
    setDescripcion('')
    setCanal('telefonico')
    setError('')
    setErroresCampos({})
    alLimpiarExito?.()
  }

  async function manejarEnvio(evento) {
    evento.preventDefault()
    setEnviando(true)
    setError('')
    setErroresCampos({})
    alLimpiarExito?.()
    const erroresLocales = {}
    if (nombreCliente.trim().length < 3) {
      erroresLocales.nombre_solicitante = ['Escribe al menos 3 caracteres.']
    }
    if (nombreCliente.trim().length > 180) {
      erroresLocales.nombre_solicitante = ['El nombre no puede superar 180 caracteres.']
    }
    if (asunto.trim().length < 4) {
      erroresLocales.asunto = ['Escribe un asunto de al menos 4 caracteres.']
    }
    if (asunto.trim().length > 180) {
      erroresLocales.asunto = ['El asunto no puede superar 180 caracteres.']
    }
    if (descripcion.trim().length < 10) {
      erroresLocales.descripcion = ['La descripción debe tener al menos 10 caracteres.']
    }
    const errorCorreo = validarCorreoOpcional(correoCliente)
    if (errorCorreo) erroresLocales.correo_solicitante = [errorCorreo]
    if (telefonoCliente.trim()) {
      const errorTelefono = validarTelefono(telefonoCliente)
      if (errorTelefono) erroresLocales.telefono_solicitante = [errorTelefono]
    }
    if (Object.keys(erroresLocales).length) {
      setErroresCampos(erroresLocales)
      setError('Revisa los campos indicados antes de radicar la solicitud.')
      setEnviando(false)
      return
    }
    try {
      await alRadicar?.({
        nombre_solicitante: nombreCliente.trim(),
        documento_solicitante: documentoCliente.trim(),
        telefono_solicitante: telefonoCliente.trim(),
        correo_solicitante: correoCliente.trim(),
        tipo,
        ambito,
        asunto: asunto.trim(),
        descripcion: descripcion.trim(),
        canal,
      })
      setNombreCliente('')
      setDocumentoCliente('')
      setTelefonoCliente('')
      setCorreoCliente('')
      setTipo('queja')
      setAmbito('servicio')
      setAsunto('')
      setDescripcion('')
      setCanal('telefonico')
    } catch (errorDeRadicacion) {
      setError(mensajeDeError(errorDeRadicacion))
      setErroresCampos(erroresDeCampo(errorDeRadicacion))
    } finally {
      setEnviando(false)
    }
  }

  function mensajeCampo(campo) {
    const errorCampo = erroresCampos[campo]
    return Array.isArray(errorCampo) ? errorCampo[0] : errorCampo
  }

  return (
    <form
      onSubmit={manejarEnvio}
      aria-label="Formulario para radicar PQR"
      className="rounded-2xl border border-azul-150 bg-blanco p-6 shadow-[0_2px_12px_rgba(17,40,83,0.03)]"
    >
      <div className="border-b border-azul-150 pb-4">
        <h2 className="text-base font-bold text-azul-950">Radicar nueva PQR de cliente</h2>
        <p className="mt-1 text-xs text-azul-400">
          Registra peticiones, quejas, reclamos o sugerencias manifestadas por un cliente por
          motivos de servicio o productos.
        </p>
      </div>

      {radicadoExitoso && (
        <div
          role="alert"
          className="mt-4 flex items-center gap-2.5 rounded-xl border border-exito-700/20 bg-exito-50 p-4 text-xs font-semibold text-exito-800"
        >
          <CheckCircleIcon size={20} weight="fill" className="text-exito-700 shrink-0" />
          <span>Solicitud radicada correctamente. Número de radicado: {radicadoExitoso}.</span>
        </div>
      )}
      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl bg-error-50 p-3 text-xs font-semibold text-error-700"
        >
          {error}
        </p>
      )}

      {/* 1. Datos del Cliente Solicitante */}
      <fieldset className="mt-5 space-y-4">
        <legend className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-azul-950">
          <UserIcon size={16} weight="bold" className="text-azul-600" />
          1. Datos del Cliente (Solicitante)
        </legend>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="pqr-nombre-cliente"
              className="block text-xs font-semibold text-azul-950"
            >
              Nombre completo o Razón social <span className="text-error-700">*</span>
            </label>
            <input
              id="pqr-nombre-cliente"
              type="text"
              required
              minLength={3}
              maxLength={180}
              aria-invalid={Boolean(mensajeCampo('nombre_solicitante'))}
              aria-describedby={mensajeCampo('nombre_solicitante') ? 'pqr-error-nombre' : undefined}
              value={nombreCliente}
              onChange={cambiarCampo(setNombreCliente, 'nombre_solicitante')}
              placeholder="Ej. Minimercado La 70 / Don Pedro Gómez"
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
            />
            {mensajeCampo('nombre_solicitante') && (
              <p id="pqr-error-nombre" className="mt-1 text-xs text-error-700">
                {mensajeCampo('nombre_solicitante')}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="pqr-documento-cliente"
              className="block text-xs font-semibold text-azul-950"
            >
              NIT / Documento <span className="text-xs text-azul-400">(Opcional)</span>
            </label>
            <input
              id="pqr-documento-cliente"
              type="text"
              maxLength={30}
              value={documentoCliente}
              onChange={(e) => setDocumentoCliente(e.target.value)}
              placeholder="NIT o cédula del cliente"
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
            />
          </div>

          <div>
            <label
              htmlFor="pqr-telefono-cliente"
              className="block text-xs font-semibold text-azul-950"
            >
              Teléfono / Celular <span className="text-xs text-azul-400">(Opcional)</span>
            </label>
            <input
              id="pqr-telefono-cliente"
              type="tel"
              maxLength={30}
              aria-invalid={Boolean(mensajeCampo('telefono_solicitante'))}
              aria-describedby={
                mensajeCampo('telefono_solicitante') ? 'pqr-error-telefono' : undefined
              }
              value={telefonoCliente}
              onChange={cambiarCampo(setTelefonoCliente, 'telefono_solicitante')}
              placeholder="Ej. 310 123 4567"
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
            />
            {mensajeCampo('telefono_solicitante') && (
              <p id="pqr-error-telefono" className="mt-1 text-xs text-error-700">
                {mensajeCampo('telefono_solicitante')}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="pqr-correo-cliente"
              className="block text-xs font-semibold text-azul-950"
            >
              Correo electrónico <span className="text-xs text-azul-400">(Opcional)</span>
            </label>
            <input
              id="pqr-correo-cliente"
              type="email"
              maxLength={150}
              aria-invalid={Boolean(mensajeCampo('correo_solicitante'))}
              aria-describedby={mensajeCampo('correo_solicitante') ? 'pqr-error-correo' : undefined}
              value={correoCliente}
              onChange={cambiarCampo(setCorreoCliente, 'correo_solicitante')}
              placeholder="cliente@ejemplo.com"
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
            />
            {mensajeCampo('correo_solicitante') && (
              <p id="pqr-error-correo" className="mt-1 text-xs text-error-700">
                {mensajeCampo('correo_solicitante')}
              </p>
            )}
          </div>
        </div>
      </fieldset>

      {/* 2. Ámbito / Motivo: Servicio o Productos */}
      <fieldset className="mt-6">
        <legend className="block text-xs font-bold uppercase tracking-wider text-azul-950">
          2. Motivo principal de la PQR <span className="text-error-700">*</span>
        </legend>
        <p className="mt-1 text-xs text-azul-400">
          Indica si la inconformidad o solicitud del cliente está relacionada con el servicio o con
          los productos.
        </p>

        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {AMBITOS_PQR.map((item) => {
            const activo = ambito === item.id
            return (
              <label
                key={item.id}
                className={`relative flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition-all ${
                  activo
                    ? 'border-azul-600 bg-azul-50 ring-2 ring-azul-600/20'
                    : 'border-azul-150 bg-blanco hover:border-azul-300 hover:bg-azul-50/50'
                }`}
              >
                <input
                  type="radio"
                  name="ambito-pqr"
                  value={item.id}
                  checked={activo}
                  onChange={() => setAmbito(item.id)}
                  className="mt-0.5 accent-azul-950"
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 font-bold text-azul-950 text-sm">
                    <span>{item.icono}</span>
                    <span>{item.etiqueta}</span>
                  </div>
                  <p className="mt-1 text-xs text-azul-400">{item.descripcion}</p>
                </div>
              </label>
            )
          })}
        </div>
      </fieldset>

      {/* 3. Tipo de PQR */}
      <fieldset className="mt-6">
        <legend className="block text-xs font-bold uppercase tracking-wider text-azul-950">
          3. Tipo de solicitud
        </legend>
        <div className="mt-2.5 flex flex-wrap gap-2">
          {TIPOS_PQR.map((t) => {
            const activo = tipo === t.id
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTipo(t.id)}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                  activo
                    ? 'bg-azul-950 text-blanco shadow-xs'
                    : 'border border-azul-150 bg-azul-50 text-azul-600 hover:bg-azul-100'
                }`}
              >
                {t.etiqueta}
              </button>
            )
          })}
        </div>
      </fieldset>

      {/* 4. Asunto y Detalle */}
      <div className="mt-6 space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="sm:col-span-2">
            <label htmlFor="pqr-asunto" className="block text-xs font-semibold text-azul-950">
              Asunto / Resumen <span className="text-error-700">*</span>
            </label>
            <input
              id="pqr-asunto"
              type="text"
              required
              minLength={4}
              maxLength={180}
              aria-invalid={Boolean(mensajeCampo('asunto'))}
              aria-describedby={mensajeCampo('asunto') ? 'pqr-error-asunto' : undefined}
              value={asunto}
              onChange={cambiarCampo(setAsunto, 'asunto')}
              placeholder="Ej. Botellas rotas en canastilla / Retraso en entrega de ruta / Error en factura"
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
            />
            {mensajeCampo('asunto') && (
              <p id="pqr-error-asunto" className="mt-1 text-xs text-error-700">
                {mensajeCampo('asunto')}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="pqr-canal" className="block text-xs font-semibold text-azul-950">
              Canal de recepción
            </label>
            <select
              id="pqr-canal"
              value={canal}
              onChange={(e) => setCanal(e.target.value)}
              className="mt-1.5 h-10 w-full rounded-xl border border-azul-200 bg-azul-50 px-3 text-sm text-azul-950 outline-none transition-colors focus:border-azul-600 focus:bg-blanco"
            >
              {CANALES_RECEPCION.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.etiqueta}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="pqr-descripcion" className="block text-xs font-semibold text-azul-950">
            Descripción detallada de la solicitud <span className="text-error-700">*</span>
          </label>
          <textarea
            id="pqr-descripcion"
            required
            minLength={10}
            aria-invalid={Boolean(mensajeCampo('descripcion'))}
            aria-describedby={mensajeCampo('descripcion') ? 'pqr-error-descripcion' : undefined}
            rows={4}
            value={descripcion}
            onChange={cambiarCampo(setDescripcion, 'descripcion')}
            placeholder="Escribe con detalle lo manifestado por el cliente, incluyendo número de factura/pedido si aplica, fecha de entrega o unidades afectadas..."
            className="mt-1.5 w-full resize-none rounded-xl border border-azul-200 bg-azul-50 p-3 text-sm text-azul-950 placeholder-azul-300 outline-none transition-colors focus:border-azul-600 focus:bg-blanco focus:ring-2 focus:ring-azul-600/15"
          />
          {mensajeCampo('descripcion') && (
            <p id="pqr-error-descripcion" className="mt-1 text-xs text-error-700">
              {mensajeCampo('descripcion')}
            </p>
          )}
        </div>
      </div>

      {/* Botones de acción */}
      <div className="mt-6 flex items-center justify-end gap-3 border-t border-azul-150 pt-4">
        <button
          type="button"
          onClick={limpiarFormulario}
          className="inline-flex h-10 items-center justify-center gap-1.5 rounded-xl border border-azul-200 px-4 text-xs font-bold text-azul-600 transition-colors hover:bg-azul-50 hover:text-azul-950 cursor-pointer"
        >
          <BroomIcon size={16} weight="bold" /> Limpiar
        </button>
        <button
          type="submit"
          disabled={enviando}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-exito-700 px-5 text-sm font-bold text-blanco shadow-sm transition-colors hover:bg-exito-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-exito-600 active:scale-[0.98] enabled:cursor-pointer disabled:opacity-60"
        >
          <PaperPlaneRightIcon size={16} weight="bold" />{' '}
          {enviando ? 'Radicando...' : 'Radicar PQR'}
        </button>
      </div>
    </form>
  )
}

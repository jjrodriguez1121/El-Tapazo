import { BuildingsIcon, EnvelopeSimpleIcon, IdentificationCardIcon, MapPinIcon } from '@phosphor-icons/react'

import { formatearPesos } from '@/utilidades/formatos'

const ETIQUETAS_DOCUMENTO = {
  cedula: 'Cédula',
  cedula_extranjeria: 'Cédula extranjería',
  pasaporte: 'Pasaporte',
  tarjeta_identidad: 'T. identidad',
}

function iniciales(nombre) {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0])
    .join('')
    .toUpperCase()
}

export default function TarjetaDeCliente({ cliente }) {
  const esEstablecimiento = cliente.tipo === 'establecimiento'
  const tieneSaldo = cliente.saldoPendiente > 0
  const identificacion = esEstablecimiento
    ? `NIT${cliente.documento ? ` · ${cliente.documento}` : ''}`
    : `${ETIQUETAS_DOCUMENTO[cliente.tipoDocumento] ?? cliente.tipoDocumento ?? 'Documento'}${cliente.documento ? ` · ${cliente.documento}` : ''}`
  const segmento = cliente.segmento
    ? `${cliente.segmento.charAt(0).toUpperCase()}${cliente.segmento.slice(1)}`
    : 'Establecimiento'

  return (
    <article className="flex min-h-32 flex-col gap-2.5 rounded-xl border border-azul-150 bg-blanco p-3.5">
      <header className="flex min-w-0 items-start gap-2.5">
        <span className="grid size-8 flex-none place-items-center rounded-lg bg-azul-950 text-[10px] font-bold text-blanco">
          {iniciales(cliente.nombre)}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-xs font-bold text-azul-950">{cliente.nombre}</h2>
          <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-azul-400">
            <span>{cliente.telefono || 'Teléfono sin registrar'}</span>
            {cliente.contacto && <span>· {cliente.contacto}</span>}
          </div>
        </div>
        <span
          className={`rounded-md px-2 py-1 text-[9px] font-semibold ${esEstablecimiento ? 'bg-azul-50 text-azul-600' : 'bg-azul-75 text-azul-600'}`}
        >
          {esEstablecimiento ? 'Establecimiento' : 'Persona'}
        </span>
      </header>

      <div className="flex min-w-0 items-center gap-2 rounded-lg bg-azul-50/60 px-2.5 py-2">
        {esEstablecimiento ? (
          <BuildingsIcon size={14} className="flex-none text-azul-600" />
        ) : (
          <IdentificationCardIcon size={14} className="flex-none text-azul-600" />
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate text-[10px] font-semibold text-azul-800">
            {esEstablecimiento ? `${segmento} · ${identificacion}` : identificacion}
          </p>
          {cliente.contacto && <p className="truncate text-[9px] text-azul-400">Contacto: {cliente.contacto}</p>}
        </div>
      </div>

      {(cliente.correo || cliente.ciudad) && (
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-[9px] text-azul-400">
          {cliente.correo && (
            <span className="flex min-w-0 items-center gap-1 truncate">
              <EnvelopeSimpleIcon size={12} className="flex-none" /> {cliente.correo}
            </span>
          )}
          {cliente.ciudad && (
            <span className="flex items-center gap-1">
              <MapPinIcon size={12} /> {cliente.ciudad}
            </span>
          )}
        </div>
      )}

      <footer className="mt-auto flex items-center justify-between gap-2 text-[10px]">
        <span className="text-azul-500">Saldo</span>
        <span
          className={`rounded-full px-2 py-1 font-semibold ${tieneSaldo ? 'bg-error-50 text-error-700' : 'bg-exito-50 text-exito-700'}`}
        >
          {tieneSaldo ? formatearPesos(cliente.saldoPendiente) : 'Al día'}
        </span>
      </footer>
    </article>
  )
}
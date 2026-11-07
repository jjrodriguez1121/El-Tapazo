import { ClockIcon, UserIcon } from '@phosphor-icons/react'

import { formatearFechaCorta } from '@/utilidades/formatos'

const ESTILOS_TIPO = {
  queja: 'bg-error-50 text-error-700 border-error-200',
  reclamo: 'bg-alerta-50 text-alerta-700 border-alerta-200',
  peticion: 'bg-azul-50 text-azul-800 border-azul-200',
  sugerencia: 'bg-exito-50 text-exito-700 border-exito-200',
}

const ESTILOS_ESTADO = {
  pendiente: 'bg-alerta-50 text-alerta-700',
  en_proceso: 'bg-azul-50 text-azul-800',
  resuelta: 'bg-exito-50 text-exito-700',
}

export default function TarjetaPqr({ pqr }) {
  const esServicio = pqr.ambito === 'servicio'

  return (
    <article className="flex flex-col justify-between rounded-2xl border border-azul-150 bg-blanco p-5 shadow-[0_2px_8px_rgba(17,40,83,0.03)] transition-all hover:border-azul-200 hover:shadow-md">
      <div>
        {/* Cabecera de la tarjeta con Tipo, Ámbito y Estado */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-azul-150/70 pb-3">
          <div className="flex items-center gap-1.5">
            <span
              className={`rounded-lg border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                ESTILOS_TIPO[pqr.tipo] || 'bg-azul-50 text-azul-950 border-azul-150'
              }`}
            >
              {pqr.tipo}
            </span>
            <span className="rounded-lg bg-azul-50 px-2 py-0.5 text-[11px] font-bold text-azul-950">
              {esServicio ? '🚚 Servicio' : '📦 Productos'}
            </span>
          </div>

          <span
            className={`rounded-lg px-2 py-0.5 text-[11px] font-bold capitalize ${
              ESTILOS_ESTADO[pqr.estado] || 'bg-azul-50 text-azul-600'
            }`}
          >
            {pqr.estado.replace('_', ' ')}
          </span>
        </div>

        {/* Asunto y Detalle */}
        <h3 className="mt-3 text-sm font-bold text-azul-950 leading-snug">
          {pqr.asunto}
        </h3>
        <p className="mt-1.5 text-xs text-azul-400 line-clamp-3">
          {pqr.descripcion}
        </p>

        {/* Datos del Cliente */}
        <div className="mt-3.5 flex items-center gap-1.5 rounded-xl bg-azul-50 p-2.5 text-xs text-azul-950 font-medium">
          <UserIcon size={14} weight="bold" className="text-azul-600 shrink-0" />
          <span className="truncate">
            <strong className="text-azul-950">Cliente:</strong> {pqr.cliente?.nombre || 'Anónimo'}
            {pqr.cliente?.telefono && ` · ${pqr.cliente.telefono}`}
          </span>
        </div>
      </div>

      {/* Pie de tarjeta con código y fecha */}
      <div className="mt-4 flex items-center justify-between border-t border-azul-150/70 pt-2.5 text-[11px] text-azul-400">
        <span className="font-mono font-semibold text-azul-600">{pqr.id}</span>
        <span className="flex items-center gap-1">
          <ClockIcon size={13} />
          {formatearFechaCorta(pqr.fecha)}
        </span>
      </div>
    </article>
  )
}


import { useCallback, useEffect, useState } from 'react'
import { CaretLeftIcon, CaretRightIcon } from '@phosphor-icons/react'

import { MENSAJES_INFORMATIVOS_BODEGA } from './mensajesInformativos'

/**
 * Cinta rotativa en el encabezado con mensajes de buenas prácticas ambientales,
 * seguridad y gestión de bodega en una distribuidora de bebidas.
 *
 * Rota automáticamente en el tiempo configurado y se pausa al pasar el cursor
 * para no interrumpir la lectura del usuario.
 */
export default function CintaInformativa({
  mensajes = MENSAJES_INFORMATIVOS_BODEGA,
  intervaloMs = 12000,
}) {
  const [indiceActual, setIndiceActual] = useState(0)
  const [enPausa, setEnPausa] = useState(false)

  const siguiente = useCallback(() => {
    setIndiceActual((previo) => (previo + 1) % mensajes.length)
  }, [mensajes.length])

  const anterior = useCallback(() => {
    setIndiceActual((previo) => (previo - 1 + mensajes.length) % mensajes.length)
  }, [mensajes.length])

  useEffect(() => {
    if (enPausa || mensajes.length <= 1) return undefined

    const temporizador = setInterval(siguiente, intervaloMs)
    return () => clearInterval(temporizador)
  }, [enPausa, siguiente, intervaloMs, mensajes.length])

  if (!mensajes.length) return null

  const mensaje = mensajes[indiceActual]
  const Icono = mensaje.icono

  return (
    <aside
      aria-label="Buenas prácticas y gestión ambiental"
      aria-live="polite"
      onMouseEnter={() => setEnPausa(true)}
      onMouseLeave={() => setEnPausa(false)}
      className="hidden sm:flex min-w-0 max-w-3xl flex-1 items-center gap-3 rounded-xl border border-azul-150 bg-azul-50/70 px-4 py-2.5 transition-colors hover:border-azul-200 hover:bg-azul-50"
    >
      {/* Icono con fondo tonal */}
      <div
        className={`flex size-9 flex-none items-center justify-center rounded-xl ${mensaje.colorFondoIcono} ${mensaje.colorIcono}`}
        aria-hidden="true"
      >
        <Icono size={20} weight="bold" />
      </div>

      {/* Etiqueta de la categoría */}
      <span className="flex-none rounded-lg border border-azul-150 bg-blanco px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-azul-950">
        {mensaje.categoria}
      </span>

      {/* Texto del mensaje */}
      <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-azul-950" title={mensaje.texto}>
        {mensaje.texto}
      </p>

      {/* Controles discretos: contador e interacción manual */}
      <div className="flex flex-none items-center gap-1.5 pl-1">
        <span className="font-mono text-xs font-semibold text-azul-400">
          {indiceActual + 1}/{mensajes.length}
        </span>
        <button
          type="button"
          onClick={anterior}
          aria-label="Mensaje anterior"
          className="flex size-7 items-center justify-center rounded-lg text-azul-400 transition-colors hover:bg-blanco hover:text-azul-950"
        >
          <CaretLeftIcon size={14} weight="bold" />
        </button>
        <button
          type="button"
          onClick={siguiente}
          aria-label="Siguiente mensaje"
          className="flex size-7 items-center justify-center rounded-lg text-azul-400 transition-colors hover:bg-blanco hover:text-azul-950"
        >
          <CaretRightIcon size={14} weight="bold" />
        </button>
      </div>
    </aside>
  )
}


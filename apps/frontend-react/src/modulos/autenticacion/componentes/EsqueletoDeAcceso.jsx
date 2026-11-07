import Esqueleto from '@/componentes/ui/Esqueleto'

/**
 * La forma de una pantalla de acceso mientras llega: el encabezado, la caja si
 * la tiene y tantos campos como vaya a tener. Así lo de verdad aparece donde ya
 * se estaba mirando, sin saltos.
 */
export default function EsqueletoDeAcceso({ campos = 2, conCaja = false, mensaje = 'Cargando…' }) {
  return (
    <div className="flex flex-col gap-6.5">
      <div className="flex flex-col gap-3">
        <Esqueleto className="h-2.75 w-30" />
        <Esqueleto className="h-6.5 w-[76%] rounded-[9px]" />
        <Esqueleto className="h-3.25 w-[90%]" retraso="100ms" />
      </div>

      {conCaja && (
        <div className="flex flex-col gap-3.5 rounded-2xl border border-azul-150 bg-azul-50 px-4.5 py-4">
          <Esqueleto className="h-3 w-full" retraso="150ms" />
          <Esqueleto className="h-3 w-[82%]" retraso="250ms" />
          <Esqueleto className="h-3 w-[58%]" retraso="350ms" />
        </div>
      )}

      <div className="flex flex-col gap-4">
        {/* La lista es fija: nunca se reordena, así que la posición sirve de clave. */}
        {Array.from({ length: campos }, (_, posicion) => (
          <Esqueleto
            key={posicion}
            className="h-13 w-full rounded-xl"
            retraso={`${200 + posicion * 100}ms`}
          />
        ))}
      </div>

      <p role="status" className="text-etiqueta font-semibold text-azul-400">
        {mensaje}
      </p>
    </div>
  )
}

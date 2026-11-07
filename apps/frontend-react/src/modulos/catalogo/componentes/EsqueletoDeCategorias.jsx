import Esqueleto from '@/componentes/ui/Esqueleto'

const TARJETAS_ESQUELETO = Array.from({ length: 8 })

/** Esqueleto de carga proporcional para la vista de categorías. */
export default function EsqueletoDeCategorias() {
  return (
    <div className="flex flex-col gap-6">
      <p role="status" className="sr-only">
        Cargando categorías…
      </p>

      {/* Encabezado y botón */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2">
          <Esqueleto className="h-7 w-44 rounded-lg" />
          <Esqueleto className="h-4 w-72 max-w-full" retraso="80ms" />
        </div>
        <Esqueleto className="h-10.5 w-38 rounded-xl" retraso="120ms" />
      </div>

      {/* Rejilla de tarjetas */}
      <div className="grid grid-cols-1 gap-4.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
        {TARJETAS_ESQUELETO.map((_, i) => (
          <div
            key={i}
            className="flex flex-col rounded-2xl border border-azul-150 bg-blanco p-5.5"
          >
            <Esqueleto className="h-11 w-11 rounded-xl" retraso={`${100 + i * 50}ms`} />
            <Esqueleto className="mt-4 h-4.5 w-24 rounded" retraso={`${150 + i * 50}ms`} />
            <Esqueleto className="mt-2 h-3.5 w-18 rounded" retraso={`${200 + i * 50}ms`} />
          </div>
        ))}
      </div>
    </div>
  )
}

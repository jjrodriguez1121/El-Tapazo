import Esqueleto from '@/componentes/ui/Esqueleto'

/** Esqueleto de carga proporcional para la vista de PQRs. */
export default function EsqueletoDePqrs() {
  return (
    <div className="flex flex-col gap-6">
      <p role="status" className="sr-only">
        Cargando módulo de PQRs…
      </p>

      {/* Encabezado */}
      <div className="flex flex-col gap-2">
        <Esqueleto className="h-7 w-48 rounded-lg" />
        <Esqueleto className="h-4 w-96 max-w-full" retraso="80ms" />
      </div>

      {/* Formulario y panel de carga */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-2xl border border-azul-150 bg-blanco p-6">
          <div className="space-y-4">
            <Esqueleto className="h-5 w-40 rounded" />
            <Esqueleto className="h-11 w-full rounded-xl" retraso="100ms" />
            <Esqueleto className="h-5 w-32 rounded" retraso="150ms" />
            <Esqueleto className="h-11 w-full rounded-xl" retraso="200ms" />
            <Esqueleto className="h-24 w-full rounded-xl" retraso="250ms" />
            <Esqueleto className="h-11 w-36 rounded-xl" retraso="300ms" />
          </div>
        </div>

        <div className="space-y-4">
          <Esqueleto className="h-32 w-full rounded-2xl" retraso="150ms" />
          <Esqueleto className="h-32 w-full rounded-2xl" retraso="250ms" />
        </div>
      </div>
    </div>
  )
}


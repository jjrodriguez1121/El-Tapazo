import Esqueleto from '@/componentes/ui/Esqueleto'

const TARJETAS = Array.from({ length: 6 }, (_, indice) => indice)

export default function EsqueletoDeClientes() {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <Esqueleto className="h-7 w-28 rounded-lg" />
          <Esqueleto className="h-4 w-64 rounded" retraso="80ms" />
        </div>
        <Esqueleto className="h-10 w-32 rounded-xl" retraso="120ms" />
      </div>
      <Esqueleto className="h-10 w-full max-w-md rounded-xl" retraso="160ms" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {TARJETAS.map((indice) => (
          <div key={indice} className="flex min-h-32 flex-col gap-3 rounded-xl border border-azul-150 bg-blanco p-3.5">
            <div className="flex items-center gap-2.5">
              <Esqueleto className="size-8 rounded-lg" retraso={`${indice * 35}ms`} />
              <div className="flex flex-1 flex-col gap-2">
                <Esqueleto className="h-3 w-28 rounded" retraso={`${indice * 35 + 20}ms`} />
                <Esqueleto className="h-2.5 w-20 rounded" retraso={`${indice * 35 + 40}ms`} />
              </div>
            </div>
            <Esqueleto className="h-8 w-full rounded-lg" retraso={`${indice * 35 + 60}ms`} />
            <Esqueleto className="h-3 w-24 self-end rounded-full" retraso={`${indice * 35 + 80}ms`} />
          </div>
        ))}
      </div>
    </div>
  )
}
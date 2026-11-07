import Esqueleto from '@/componentes/ui/Esqueleto'

const FILAS = Array.from({ length: 7 }, (_, indice) => indice)

export default function EsqueletoDeProductos() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2">
          <Esqueleto className="h-7 w-36 rounded-lg" />
          <Esqueleto className="h-4 w-60 max-w-full" retraso="80ms" />
        </div>
        <Esqueleto className="h-10.5 w-38 rounded-xl" retraso="120ms" />
      </div>
      <Esqueleto className="h-10 w-full rounded-xl" retraso="160ms" />
      <div className="overflow-hidden rounded-xl border border-azul-150 bg-blanco">
        {FILAS.map((fila) => (
          <div key={fila} className="flex h-16 items-center gap-6 border-b border-azul-100 px-5">
            <Esqueleto className="size-9 rounded-lg" retraso={`${fila * 35}ms`} />
            <Esqueleto className="h-4 flex-1 rounded" retraso={`${fila * 35 + 25}ms`} />
            <Esqueleto className="h-4 w-24 rounded" retraso={`${fila * 35 + 50}ms`} />
            <Esqueleto className="h-4 w-20 rounded" retraso={`${fila * 35 + 75}ms`} />
          </div>
        ))}
      </div>
    </div>
  )
}
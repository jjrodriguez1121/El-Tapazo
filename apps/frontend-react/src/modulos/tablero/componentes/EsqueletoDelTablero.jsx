import Esqueleto from '@/componentes/ui/Esqueleto'

const INDICADORES = ['ventas', 'productos', 'pedidos', 'stock-bajo']

/** La forma del tablero mientras llega: el encabezado, las cuatro cifras y los paneles. */
export default function EsqueletoDelTablero() {
  return (
    <div className="flex flex-col gap-4.5">
      <p role="status" className="sr-only">
        Cargando el tablero…
      </p>

      <div className="mb-1.5 flex flex-col gap-2.5">
        <Esqueleto className="h-6.5 w-40 rounded-lg" />
        <Esqueleto className="h-3.5 w-72 max-w-full" retraso="100ms" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {INDICADORES.map((indicador, posicion) => (
          <Esqueleto
            key={indicador}
            className="h-34 rounded-tarjeta"
            retraso={`${150 + posicion * 80}ms`}
          />
        ))}
      </div>

      <div className="grid gap-4.5 lg:grid-cols-[1.55fr_1fr]">
        <Esqueleto className="h-60 rounded-tarjeta" retraso="300ms" />
        <Esqueleto className="h-60 rounded-tarjeta" retraso="380ms" />
      </div>
    </div>
  )
}

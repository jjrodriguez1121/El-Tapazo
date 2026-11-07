import { Link } from 'react-router-dom'

import { RUTAS } from '@/configuracion/rutas'

/** Una sección del menú que todavía no tiene pantalla. Se ve dentro del panel, sin perder el menú. */
export default function PaginaEnConstruccion({ titulo }) {
  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-1.25">
        <h1 className="text-titulo font-semibold tracking-[-0.01em]">{titulo}</h1>
        <p className="text-etiqueta font-medium text-azul-400">
          Esta sección todavía no está lista.
        </p>
      </header>

      <div className="flex flex-col items-center gap-3 rounded-tarjeta border border-dashed border-azul-150 bg-blanco px-6 py-12 text-center">
        <p className="text-base font-semibold">Estamos construyendo esta pantalla.</p>
        <p className="max-w-sm text-etiqueta font-medium text-pretty text-azul-400">
          Mientras tanto, el resumen del negocio está en el tablero.
        </p>
        <Link
          to={RUTAS.inicio}
          className="mt-2 rounded-xl bg-azul-950 px-4.5 py-2.75 text-etiqueta font-semibold text-blanco hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-300"
        >
          Ir al tablero
        </Link>
      </div>
    </section>
  )
}

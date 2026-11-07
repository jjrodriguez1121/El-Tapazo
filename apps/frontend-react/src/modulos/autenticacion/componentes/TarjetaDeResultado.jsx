const MARCAS = {
  exito: { simbolo: '✓', fondo: 'bg-azul-950' },
  error: { simbolo: '!', fondo: 'bg-error-700' },
}

/**
 * El final de un camino: salió bien, o no hay forma de seguir por aquí.
 * Reemplaza al formulario entero y deja solo la salida, en `acciones`.
 */
export default function TarjetaDeResultado({ tono, titulo, children, acciones }) {
  const marca = MARCAS[tono]

  return (
    <section aria-live="polite" className="flex flex-col items-start gap-5">
      <div
        aria-hidden="true"
        className={`grid size-13 place-items-center rounded-2xl text-2xl leading-none font-extrabold text-blanco ${marca.fondo}`}
      >
        {marca.simbolo}
      </div>

      <div className="flex flex-col gap-2.5">
        <h1 className="text-titulo leading-[1.2] font-extrabold tracking-[-0.025em] text-pretty">
          {titulo}
        </h1>
        <p className="text-destacado leading-relaxed font-medium text-pretty text-azul-600">
          {children}
        </p>
      </div>

      <div className="mt-1 flex w-full flex-col gap-3.5">{acciones}</div>
    </section>
  )
}

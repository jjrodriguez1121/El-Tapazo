const RETRASOS_DE_ONDA = ['0ms', '660ms', '1330ms']

/** Mientras se comprueba el enlace del correo: ondas que salen de un punto que respira. */
export default function ComprobandoEnlace() {
  return (
    <div role="status" className="flex flex-col items-center gap-5.5 py-6 text-center">
      <span aria-hidden="true" className="relative grid size-24 place-items-center">
        {RETRASOS_DE_ONDA.map((retraso, posicion) => (
          <span
            key={retraso}
            className={`absolute inset-0 block animate-onda rounded-full border-2 opacity-0 ${posicion === 0 ? 'border-azul-400' : 'border-azul-300'}`}
            style={{ animationDelay: retraso }}
          />
        ))}
        <span className="block size-6.5 animate-respirar rounded-full bg-azul-950" />
      </span>

      <div className="flex flex-col gap-2.25">
        <h1 className="text-titulo-chico font-extrabold tracking-[-0.02em]">
          Comprobando el enlace…
        </h1>
        <p className="text-sm leading-relaxed font-medium text-pretty text-azul-600">
          Esto toma unos segundos. No cierres esta pantalla.
        </p>
      </div>
    </div>
  )
}

const APARIENCIAS = {
  error: {
    rol: 'alert',
    caja: 'border-error-200 bg-error-50',
    marca: 'bg-error-700',
    texto: 'text-error-700',
    simbolo: '!',
  },
  exito: {
    rol: 'status',
    caja: 'border-azul-150 bg-azul-50',
    marca: 'bg-azul-600',
    texto: 'text-azul-950',
    simbolo: '✓',
  },
}

/** Un aviso dentro del formulario: qué pasó y, si hay una salida, el botón para tomarla. */
export default function Aviso({ children, tono = 'error', textoDeAccion, alPulsarAccion }) {
  const apariencia = APARIENCIAS[tono]

  return (
    <div
      role={apariencia.rol}
      className={`flex flex-col gap-3 rounded-2xl border px-4.25 py-3.75 ${apariencia.caja}`}
    >
      <div className="flex gap-2.75">
        <span
          aria-hidden="true"
          className={`grid size-5 flex-none place-items-center rounded-full text-etiqueta leading-none font-extrabold text-blanco ${apariencia.marca}`}
        >
          {apariencia.simbolo}
        </span>
        <p className={`text-sm leading-[1.55] font-semibold text-pretty ${apariencia.texto}`}>
          {children}
        </p>
      </div>

      {textoDeAccion && (
        <button
          type="button"
          onClick={alPulsarAccion}
          className="self-start rounded-[10px] border border-error-200 bg-blanco px-3.5 py-2.25 text-etiqueta font-bold text-error-700 hover:bg-error-50 focus-visible:outline-2 focus-visible:outline-error-300"
        >
          {textoDeAccion}
        </button>
      )}
    </div>
  )
}

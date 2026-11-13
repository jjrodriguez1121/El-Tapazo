import { useEffect, useId, useRef } from 'react'
import { CheckCircleIcon, WarningCircleIcon } from '@phosphor-icons/react'

export default function ConfirmacionAccion({
  titulo,
  descripcion,
  textoConfirmar,
  textoCancelar = 'Cancelar',
  variante = 'advertencia',
  procesando = false,
  alConfirmar,
  alCancelar,
}) {
  const tituloId = useId()
  const descripcionId = useId()
  const botonCancelar = useRef(null)
  const alCancelarRef = useRef(alCancelar)
  const procesandoRef = useRef(procesando)
  const esDestructiva = variante === 'destructiva'
  const Icono = esDestructiva ? WarningCircleIcon : CheckCircleIcon
  alCancelarRef.current = alCancelar
  procesandoRef.current = procesando

  useEffect(() => {
    const elementoEnfocado = document.activeElement
    botonCancelar.current?.focus()

    function manejarTecla(evento) {
      if (evento.key === 'Escape' && !procesandoRef.current) alCancelarRef.current()
    }

    document.addEventListener('keydown', manejarTecla)
    return () => {
      document.removeEventListener('keydown', manejarTecla)
      if (elementoEnfocado instanceof HTMLElement && elementoEnfocado.isConnected) {
        elementoEnfocado.focus()
      }
    }
  }, [])

  return (
    <div
      className="fixed inset-0 z-[70] grid place-items-center bg-azul-950/55 px-4 py-6"
      onClick={(evento) => {
        if (evento.target === evento.currentTarget && !procesando) alCancelar()
      }}
    >
      <section
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        aria-describedby={descripcionId}
        aria-busy={procesando}
        className="w-full max-w-md rounded-2xl border border-azul-150 bg-blanco p-5 shadow-2xl sm:p-6"
      >
        <div className="flex items-start gap-3.5">
          <span
            className={`grid size-11 flex-none place-items-center rounded-full ${
              esDestructiva ? 'bg-error-50 text-error-700' : 'bg-exito-50 text-exito-700'
            }`}
          >
            <Icono size={23} weight="fill" aria-hidden="true" />
          </span>
          <div className="min-w-0 pt-0.5">
            <h2 id={tituloId} className="text-base font-bold text-azul-950">
              {titulo}
            </h2>
            <p id={descripcionId} className="mt-1.5 text-sm leading-6 text-azul-600">
              {descripcion}
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            ref={botonCancelar}
            type="button"
            disabled={procesando}
            onClick={alCancelar}
            className="inline-flex h-10 items-center justify-center rounded-lg border border-azul-200 px-4 text-sm font-semibold text-azul-700 transition-colors hover:bg-azul-50 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {textoCancelar}
          </button>
          <button
            type="button"
            disabled={procesando}
            onClick={alConfirmar}
            className={`inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-semibold text-blanco transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 disabled:cursor-progress disabled:opacity-60 ${
              esDestructiva
                ? 'bg-error-700 hover:bg-error-800 focus-visible:outline-error-600'
                : 'bg-exito-700 hover:bg-exito-800 focus-visible:outline-exito-600'
            }`}
          >
            {procesando ? 'Procesando...' : textoConfirmar}
          </button>
        </div>
      </section>
    </div>
  )
}

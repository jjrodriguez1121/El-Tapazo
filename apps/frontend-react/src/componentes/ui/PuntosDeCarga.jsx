const RETRASOS = ['0ms', '160ms', '320ms']

/** Tres puntos que laten mientras el botón espera al servidor. */
export default function PuntosDeCarga() {
  return (
    <span aria-hidden="true" className="flex items-center gap-1.25">
      {RETRASOS.map((retraso) => (
        <span
          key={retraso}
          className="block size-2 animate-pulso rounded-full bg-blanco"
          style={{ animationDelay: retraso }}
        />
      ))}
    </span>
  )
}

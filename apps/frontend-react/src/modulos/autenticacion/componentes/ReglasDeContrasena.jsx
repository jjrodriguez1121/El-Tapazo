import { evaluarContrasena } from '../utilidades/reglasDeContrasena'

const APARIENCIAS = {
  cumplida: { simbolo: '✓', marca: 'bg-azul-600', texto: 'text-azul-950', lectura: 'cumplida' },
  fallida: { simbolo: '!', marca: 'bg-error-700', texto: 'text-error-700', lectura: 'falta' },
  pendiente: { simbolo: '·', marca: 'bg-azul-300', texto: 'text-azul-400', lectura: 'falta' },
}

function aparienciaDe(regla, marcarFallos) {
  if (regla.cumplida) return APARIENCIAS.cumplida
  return marcarFallos ? APARIENCIAS.fallida : APARIENCIAS.pendiente
}

/**
 * Lo que necesita la contraseña, marcado a medida que se escribe. Con
 * `rechazada` la caja entera se pone en rojo: ya se intentó enviar así.
 */
export default function ReglasDeContrasena({ contrasena, rechazada = false }) {
  const marcarFallos = rechazada || contrasena.length > 0

  return (
    <div
      className={`flex flex-col gap-2.25 rounded-2xl border px-4 py-3.5 ${rechazada ? 'border-error-200 bg-error-50' : 'border-azul-150 bg-azul-50'}`}
    >
      <p className={`text-xs font-bold ${rechazada ? 'text-error-700' : 'text-azul-600'}`}>
        {rechazada ? 'Esa contraseña no sirve todavía:' : 'Tu contraseña necesita:'}
      </p>

      <ul className="flex flex-col gap-2.25">
        {evaluarContrasena(contrasena).map((regla) => {
          const apariencia = aparienciaDe(regla, marcarFallos)
          return (
            <li key={regla.id} className="flex items-start gap-2.25">
              <span
                aria-hidden="true"
                className={`mt-0.5 grid size-4 flex-none place-items-center rounded-full text-[10px] leading-none font-extrabold text-blanco ${apariencia.marca}`}
              >
                {apariencia.simbolo}
              </span>
              <span className={`text-etiqueta leading-[1.45] font-semibold ${apariencia.texto}`}>
                {regla.etiqueta}
                <span className="sr-only"> ({apariencia.lectura})</span>
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

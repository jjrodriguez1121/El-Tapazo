import { useId } from 'react'

/**
 * Un campo con su etiqueta y, si hace falta, su error debajo.
 *
 * Lo que no es de aquí (`type`, `value`, `onChange`, `autoComplete`…) va directo
 * al <input>. `invalido` marca el borde sin mensaje, para cuando el error se
 * explica en otro sitio; `accesorio` va dentro del campo, a la derecha, como el
 * botón de mostrar la contraseña.
 */
export default function CampoTexto({
  etiqueta,
  error = '',
  opcional = false,
  invalido = false,
  accesorio,
  ...propsDelInput
}) {
  const id = useId()
  const idDelError = `${id}-error`
  const marcado = Boolean(error) || invalido

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1.75">
      <label htmlFor={id} className="flex items-center gap-2 text-etiqueta font-bold text-azul-600">
        {etiqueta}
        {opcional && <span className="text-xs font-semibold text-azul-400">Opcional</span>}
      </label>

      <span className="relative block">
        <input
          id={id}
          aria-invalid={marcado}
          aria-describedby={error ? idDelError : undefined}
          className={`h-13 w-full rounded-xl border bg-blanco px-3.5 text-base text-azul-950 outline-none placeholder:text-azul-300 focus:border-azul-600 focus:ring-3 focus:ring-azul-600/16 ${accesorio ? 'pr-21' : ''} ${marcado ? 'border-error-300' : 'border-azul-200'}`}
          {...propsDelInput}
        />
        {accesorio}
      </span>

      {error && (
        <p id={idDelError} className="text-etiqueta font-semibold text-error-700">
          {error}
        </p>
      )}
    </div>
  )
}

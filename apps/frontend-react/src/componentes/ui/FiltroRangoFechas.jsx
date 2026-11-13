export default function FiltroRangoFechas({ titulo, desde, hasta, alCambiar }) {
  return (
    <fieldset className="flex flex-wrap items-end gap-3">
      <legend className="mb-2 text-xs font-semibold text-azul-600">{titulo}</legend>
      <label className="flex flex-col gap-1 text-[11px] font-medium text-azul-500">
        Desde
        <input
          type="date"
          aria-label={`${titulo}: desde`}
          value={desde}
          max={hasta || undefined}
          onChange={(evento) => alCambiar({ desde: evento.target.value, hasta })}
          className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
        />
      </label>
      <label className="flex flex-col gap-1 text-[11px] font-medium text-azul-500">
        Hasta
        <input
          type="date"
          aria-label={`${titulo}: hasta`}
          value={hasta}
          min={desde || undefined}
          onChange={(evento) => alCambiar({ desde, hasta: evento.target.value })}
          className="h-9 rounded-lg border border-azul-200 px-2 text-xs text-azul-950 outline-none focus:border-azul-600"
        />
      </label>
      {(desde || hasta) && (
        <button
          type="button"
          onClick={() => alCambiar({ desde: '', hasta: '' })}
          className="h-9 rounded-lg border border-azul-200 px-3 text-xs font-semibold text-azul-700 hover:bg-azul-50"
        >
          Limpiar fechas
        </button>
      )}
    </fieldset>
  )
}

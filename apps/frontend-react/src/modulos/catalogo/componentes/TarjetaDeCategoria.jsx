import { formatearCantidad } from '@/utilidades/formatos'
import { PencilSimpleIcon, TrashIcon } from '@phosphor-icons/react'

/**
 * Tarjeta individual que representa una categoría del catálogo.
 */
export default function TarjetaDeCategoria({
  nombre,
  cantidadProductos,
  Icono,
  onClick,
  alEditar,
  alEliminar,
}) {
  const textoProductos = `${formatearCantidad(cantidadProductos)} ${
    cantidadProductos === 1 ? 'producto' : 'productos'
  }`

  return (
    <article
      onClick={onClick}
      className="group relative flex flex-col justify-between rounded-2xl border border-azul-150 bg-blanco p-5.5 shadow-[0_2px_8px_rgba(17,40,83,0.03)] transition-all duration-200 hover:-translate-y-0.5 hover:border-azul-200 hover:shadow-[0_8px_20px_rgba(17,40,83,0.06)] cursor-pointer"
    >
      <div>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-exito-50 text-exito-700 transition-colors group-hover:bg-exito-100">
          {Icono ? (
            <Icono size={22} weight="bold" />
          ) : (
            <span className="text-sm font-bold">{nombre?.slice(0, 2).toUpperCase()}</span>
          )}
        </div>

        <h3 className="mt-4 text-base font-bold text-azul-950 tracking-tight">
          {nombre}
        </h3>

        <p className="mt-1 text-xs font-medium text-azul-400">
          {textoProductos}
        </p>
      </div>
      <footer className="mt-4 flex justify-end gap-1 border-t border-azul-100 pt-3">
        <button
          type="button"
          aria-label={`Editar ${nombre}`}
          onClick={(evento) => {
            evento.stopPropagation()
            alEditar()
          }}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-50"
        >
          <PencilSimpleIcon size={15} /> Editar
        </button>
        <button
          type="button"
          aria-label={`Eliminar ${nombre}`}
          onClick={(evento) => {
            evento.stopPropagation()
            alEliminar()
          }}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-semibold text-error-600 hover:bg-error-50"
        >
          <TrashIcon size={15} /> Eliminar
        </button>
      </footer>
    </article>
  )
}

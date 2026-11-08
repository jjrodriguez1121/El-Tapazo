import { formatearCantidad } from '@/utilidades/formatos'
import { PencilSimpleIcon, PowerIcon } from '@phosphor-icons/react'

/**
 * Tarjeta individual que representa una categoría del catálogo.
 */
export default function TarjetaDeCategoria({
  nombre,
  cantidadProductos,
  activa,
  Icono,
  onClick,
  alEditar,
  alCambiarEstado,
}) {
  const textoProductos = `${formatearCantidad(cantidadProductos)} ${
    cantidadProductos === 1 ? 'producto' : 'productos'
  }`

  return (
    <article
      onClick={onClick}
      className={`group relative flex flex-col justify-between rounded-2xl border border-azul-150 bg-blanco p-5.5 shadow-[0_2px_8px_rgba(17,40,83,0.03)] transition-all duration-200 hover:-translate-y-0.5 hover:border-azul-200 hover:shadow-[0_8px_20px_rgba(17,40,83,0.06)] cursor-pointer ${activa ? '' : 'opacity-70'}`}
    >
      <div>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-exito-50 text-exito-700 transition-colors group-hover:bg-exito-100">
          {Icono ? (
            <Icono size={22} weight="bold" />
          ) : (
            <span className="text-sm font-bold">{nombre?.slice(0, 2).toUpperCase()}</span>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between gap-2">
          <h3 className="truncate text-base font-bold tracking-tight text-azul-950">{nombre}</h3>
          {!activa && (
            <span className="flex-none rounded-full bg-azul-100 px-2 py-0.5 text-[10px] font-semibold text-azul-600">
              Inactiva
            </span>
          )}
        </div>

        <p className="mt-1 text-xs font-medium text-azul-400">{textoProductos}</p>
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
          aria-label={`${activa ? 'Desactivar' : 'Activar'} ${nombre}`}
          onClick={(evento) => {
            evento.stopPropagation()
            alCambiarEstado()
          }}
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-semibold ${activa ? 'text-error-600 hover:bg-error-50' : 'text-exito-700 hover:bg-exito-50'}`}
        >
          <PowerIcon size={15} /> {activa ? 'Desactivar' : 'Activar'}
        </button>
      </footer>
    </article>
  )
}

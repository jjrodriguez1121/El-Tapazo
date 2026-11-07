import { formatearCantidad } from '@/utilidades/formatos'

/**
 * Tarjeta individual que representa una categoría del catálogo.
 */
export default function TarjetaDeCategoria({ nombre, cantidadProductos, Icono, onClick }) {
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
    </article>
  )
}

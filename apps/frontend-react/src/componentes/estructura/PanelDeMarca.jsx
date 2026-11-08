import logoTapazo from '@/recursos/imagenes/logo-tapazo.png'

/** El panel de marca azul, a la derecha en escritorio y fuera de vista en celular. */
export default function PanelDeMarca() {
  return (
    <aside className="relative order-2 hidden w-[44%] flex-col overflow-hidden bg-azul-950 px-10 py-11 lg:order-2 lg:flex">
      <img
        src={logoTapazo}
        alt="Logo de El Tapazo"
        className="relative z-10 mx-auto w-full max-w-65 rounded-2xl bg-blanco p-2 shadow-xl ring-1 ring-blanco/30"
      />

      <div className="relative z-10 my-auto flex max-w-85 flex-col gap-3.5">
        <p className="font-mono text-antetitulo font-bold tracking-[0.16em] text-azul-300 uppercase">
          Distribuidora El Tapazo
        </p>
        <p className="text-3xl leading-tight font-extrabold tracking-[-0.03em] text-pretty text-blanco">
          Tu inventario y tus ventas, bajo control.
        </p>
        <p className="max-w-80 text-sm leading-relaxed font-medium text-pretty text-azul-200">
          Administra productos, existencias y ventas desde un solo lugar. Información clara para
          abastecer mejor y hacer crecer tu distribuidora.
        </p>
      </div>

      <div className="relative z-10 flex items-center gap-2 border-t border-blanco/15 pt-5 text-xs font-semibold tracking-wide text-azul-200">
        <span>Inventario</span>
        <span aria-hidden="true" className="size-1 rounded-full bg-azul-400" />
        <span>Ventas</span>
        <span aria-hidden="true" className="size-1 rounded-full bg-azul-400" />
        <span>Distribución</span>
      </div>

      <div
        aria-hidden="true"
        className="absolute top-22.5 -right-22.5 size-65 rounded-full bg-azul-850"
      />
      <div
        aria-hidden="true"
        className="absolute -right-10 -bottom-17.5 size-45 rounded-full bg-azul-900"
      />
    </aside>
  )
}

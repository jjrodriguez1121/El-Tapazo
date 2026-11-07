/** El panel azul de la izquierda en escritorio. En el celular no hay sitio, y no aparece. */
export default function PanelDeMarca() {
  return (
    <div className="relative hidden w-[44%] flex-col overflow-hidden bg-azul-950 px-10 py-11 lg:flex">
      <div className="relative z-10 my-auto flex max-w-85 flex-col gap-3.5">
        <p className="text-titulo leading-tight font-bold tracking-[-0.02em] text-pretty text-blanco">
          Inventario y ventas para bares y distribuidoras.
        </p>
        <p className="text-sm leading-relaxed font-medium text-pretty text-azul-300">
          El acceso lo abre el administrador de tu negocio. Nadie se registra por su cuenta.
        </p>
      </div>

      <div aria-hidden="true" className="relative z-10 flex gap-1.75">
        <span className="block h-1.5 w-9.5 rounded-full bg-azul-600" />
        <span className="block h-1.5 w-9.5 rounded-full bg-azul-400" />
        <span className="block h-1.5 w-9.5 rounded-full bg-azul-300" />
      </div>

      <div
        aria-hidden="true"
        className="absolute top-22.5 -right-22.5 size-65 rounded-full bg-azul-850"
      />
      <div
        aria-hidden="true"
        className="absolute -right-10 -bottom-17.5 size-45 rounded-full bg-azul-900"
      />
    </div>
  )
}

/**
 * El armazón del panel —menú lateral, barra de arriba y contenido— mientras se
 * recupera la sesión. Lo de dentro lo pone quien lo usa.
 */
export default function EsqueletoDePlantillaPrincipal({ children }) {
  return (
    <div className="flex min-h-dvh bg-azul-50">
      <div aria-hidden="true" className="hidden w-62 flex-none bg-azul-950 lg:block" />
      <div className="flex min-w-0 flex-1 flex-col">
        <div aria-hidden="true" className="h-18.5 border-b border-azul-100 bg-blanco" />
        <div className="px-4 py-6 sm:px-8 sm:py-7">{children}</div>
      </div>
    </div>
  )
}

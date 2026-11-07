/** Lo primero de cada pantalla de acceso: dónde estás, qué hay que hacer y cómo. */
export default function EncabezadoDeAcceso({ antetitulo, titulo, children }) {
  return (
    <header className="flex flex-col gap-2.25">
      <p className="font-mono text-antetitulo font-bold tracking-[0.14em] text-azul-400 uppercase">
        {antetitulo}
      </p>
      <h1 className="text-titulo leading-[1.2] font-extrabold tracking-[-0.025em] text-pretty">
        {titulo}
      </h1>
      <p className="text-sm leading-relaxed font-medium text-pretty text-azul-600">{children}</p>
    </header>
  )
}

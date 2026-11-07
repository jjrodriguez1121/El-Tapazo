import EnlacePrincipal from '@/componentes/ui/EnlacePrincipal'

export default function PaginaNoEncontrada() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-100 flex-col justify-center gap-5 px-6.5">
      <p className="font-mono text-antetitulo font-bold tracking-[0.14em] text-azul-400 uppercase">
        Error 404
      </p>
      <h1 className="text-titulo leading-[1.2] font-extrabold tracking-[-0.025em]">
        Esta página no existe.
      </h1>
      <p className="text-sm leading-relaxed font-medium text-azul-600">
        Revisa la dirección o vuelve al inicio.
      </p>
      <EnlacePrincipal a="/">Volver al inicio</EnlacePrincipal>
    </main>
  )
}

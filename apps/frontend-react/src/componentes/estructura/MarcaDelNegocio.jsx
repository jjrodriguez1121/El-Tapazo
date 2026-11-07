import { iniciales } from '@/utilidades/iniciales'

/**
 * El negocio de quien entró, arriba del menú. El staff de la plataforma no
 * pertenece a ningún negocio, y se dice así.
 */
export default function MarcaDelNegocio({ negocio }) {
  const nombre = negocio?.nombreComercial ?? 'Staff de la plataforma'

  return (
    <div className="flex items-center gap-2.75 px-2 pt-1 pb-5.5">
      <span
        aria-hidden="true"
        className="grid size-10 flex-none place-items-center rounded-xl bg-blanco text-sm font-bold text-azul-950"
      >
        {iniciales(nombre)}
      </span>
      <p
        title={nombre}
        className="min-w-0 truncate text-base leading-tight font-semibold text-blanco"
      >
        {nombre}
      </p>
    </div>
  )
}

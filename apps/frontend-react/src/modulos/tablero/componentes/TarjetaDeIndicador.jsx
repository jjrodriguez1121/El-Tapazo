import Insignia from '@/componentes/ui/Insignia'
import { CLASES_POR_TONO } from '@/componentes/ui/tonos'

/** Una cifra clave del día, con su ícono y cómo va. */
export default function TarjetaDeIndicador({ Icono, tono, etiqueta, valor, variacion }) {
  return (
    <article className="rounded-tarjeta border border-azul-100 bg-blanco p-5">
      <div className="mb-3.5 flex items-center justify-between">
        <span
          aria-hidden="true"
          className={`grid size-10.5 place-items-center rounded-xl ${CLASES_POR_TONO[tono]}`}
        >
          <Icono size={20} />
        </span>
        <Insignia tono={tono}>{variacion}</Insignia>
      </div>
      <p className="mb-0.5 text-2xl font-semibold">{valor}</p>
      <p className="text-etiqueta font-medium text-azul-400">{etiqueta}</p>
    </article>
  )
}

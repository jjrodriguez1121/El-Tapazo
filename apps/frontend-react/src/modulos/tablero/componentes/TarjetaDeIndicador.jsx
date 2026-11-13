import Insignia from '@/componentes/ui/Insignia'
import { CLASES_POR_TONO } from '@/componentes/ui/tonos'

/** Una cifra clave del día, con su ícono y cómo va. */
export default function TarjetaDeIndicador({ Icono, tono, etiqueta, valor, variacion, compacta = false }) {
  return (
    <article className={`rounded-tarjeta border border-azul-100 bg-blanco ${compacta ? 'p-3.5' : 'p-5'}`}>
      <div className={`${compacta ? 'mb-2' : 'mb-3.5'} flex items-center justify-between`}>
        <span
          aria-hidden="true"
          className={`grid ${compacta ? 'size-8.5 rounded-lg' : 'size-10.5 rounded-xl'} place-items-center ${CLASES_POR_TONO[tono]}`}
        >
          <Icono size={compacta ? 17 : 20} />
        </span>
        {variacion && <Insignia tono={tono}>{variacion}</Insignia>}
      </div>
      <p className={`${compacta ? 'text-xl' : 'text-2xl'} mb-0.5 font-semibold`}>{valor}</p>
      <p className="text-etiqueta font-medium text-azul-400">{etiqueta}</p>
    </article>
  )
}

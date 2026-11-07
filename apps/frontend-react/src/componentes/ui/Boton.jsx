import { CLASES_BOTON_PRINCIPAL } from './estilosDeBoton'
import PuntosDeCarga from './PuntosDeCarga'

/** El botón principal. Mientras `cargando`, enseña los puntos y no deja volver a pulsarlo. */
export default function Boton({ children, cargando = false, type = 'button', onClick }) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={cargando}
      aria-busy={cargando}
      className={CLASES_BOTON_PRINCIPAL}
    >
      {cargando && <PuntosDeCarga />}
      {children}
    </button>
  )
}

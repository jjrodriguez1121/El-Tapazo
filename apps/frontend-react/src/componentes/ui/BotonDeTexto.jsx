import { CLASES_BOTON_DE_TEXTO } from './estilosDeBoton'

/** Una acción secundaria que se ve como texto subrayado. */
export default function BotonDeTexto({ children, onClick }) {
  return (
    <button type="button" onClick={onClick} className={CLASES_BOTON_DE_TEXTO}>
      {children}
    </button>
  )
}

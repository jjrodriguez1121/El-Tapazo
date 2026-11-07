import { Link } from 'react-router-dom'

import { CLASES_BOTON_DE_TEXTO } from './estilosDeBoton'

/** Un enlace secundario a otra pantalla, como texto subrayado. */
export default function EnlaceDeTexto({ children, a }) {
  return (
    <Link to={a} className={CLASES_BOTON_DE_TEXTO}>
      {children}
    </Link>
  )
}

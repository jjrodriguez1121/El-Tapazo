import { Link } from 'react-router-dom'

import { CLASES_BOTON_PRINCIPAL } from './estilosDeBoton'

/** Un enlace a otra pantalla con la cara del botón principal. */
export default function EnlacePrincipal({ children, a }) {
  return (
    <Link to={a} className={CLASES_BOTON_PRINCIPAL}>
      {children}
    </Link>
  )
}

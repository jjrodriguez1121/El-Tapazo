import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import ConfirmacionDeCorreo from '../componentes/ConfirmacionDeCorreo'
import ReenvioDeVerificacion from '../componentes/ReenvioDeVerificacion'
import { enlaceDesdeParametros, enlaceEstaCompleto } from '../dtos/enlace'

/**
 * Dos momentos en la misma pantalla. Con el enlace del correo (`?uid=…&token=…`)
 * confirma sola y avisa; sin él, o si el enlace ya no sirve, deja pedir otro.
 */
export default function PaginaVerificarCorreo() {
  const [parametros] = useSearchParams()
  const enlace = enlaceDesdeParametros(parametros)
  const [pideOtroEnlace, setPideOtroEnlace] = useState(!enlaceEstaCompleto(enlace))

  if (pideOtroEnlace) return <ReenvioDeVerificacion />

  return <ConfirmacionDeCorreo enlace={enlace} alPedirOtroEnlace={() => setPideOtroEnlace(true)} />
}

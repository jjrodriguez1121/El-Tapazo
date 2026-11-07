import TarjetaDeResultado from './TarjetaDeResultado'

/**
 * El enlace del correo venció, ya se usó o llegó incompleto. Los tres casos se
 * dicen igual a propósito: se arreglan igual, y distinguirlos le contaría a
 * quien prueba tokens al azar cuánto se acercó.
 */
export default function TarjetaDeEnlaceInvalido({ acciones }) {
  return (
    <TarjetaDeResultado
      tono="error"
      titulo="El enlace no es válido o ya venció."
      acciones={acciones}
    >
      Solicita uno nuevo y ábrelo desde el correo más reciente.
    </TarjetaDeResultado>
  )
}

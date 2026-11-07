/*
 * Validación de formato de los formularios de acceso: cerca de la persona, para
 * que no espere al servidor por un campo vacío. La última palabra la tiene el
 * backend.
 */

export {
  LARGO_MAXIMO_DE_CORREO,
  validarCorreo,
  validarObligatorio,
} from '@/utilidades/validaciones'

/** Lo único que se pide para recuperar la contraseña o reenviar la verificación. */
export const correoHaciaApi = (correo) => ({ correo: correo.trim() })

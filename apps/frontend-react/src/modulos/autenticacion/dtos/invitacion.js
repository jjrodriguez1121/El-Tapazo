/** De qué es una invitación, para enseñarla antes de pedir los datos. */
export const invitacionPendienteDesdeApi = (invitacion) => ({
  correo: invitacion.correo,
  rol: invitacion.rol,
  negocio: invitacion.negocio,
  expiraEn: invitacion.expira_en,
})

/**
 * Lo que manda el formulario de la invitación. El correo y el rol no van: los
 * puso quien invitó, y el backend ignoraría lo que llegara.
 */
export const aceptacionHaciaApi = ({ token, nombre, apellido, telefono, contrasena }) => ({
  token,
  nombre: nombre.trim(),
  apellido: apellido.trim(),
  telefono: telefono.trim(),
  contrasena,
})

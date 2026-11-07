/** El usuario tal como lo usa la aplicación, a partir del JSON de la API. */
export function usuarioDesdeApi(usuario) {
  return {
    id: usuario.id,
    correo: usuario.correo,
    nombre: usuario.nombre,
    apellido: usuario.apellido,
    nombreCompleto: usuario.nombre_completo,
    telefono: usuario.telefono,
    rol: usuario.rol,
    esAdministrador: usuario.es_administrador,
    // El staff de la plataforma no pertenece a ningún negocio.
    negocio: usuario.negocio
      ? { id: usuario.negocio.id, nombreComercial: usuario.negocio.nombre_comercial }
      : null,
    correoVerificadoEn: usuario.correo_verificado_en,
    fechaAlta: usuario.fecha_alta,
  }
}

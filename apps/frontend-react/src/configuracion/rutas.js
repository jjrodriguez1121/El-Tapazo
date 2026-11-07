/** Las rutas de la aplicación, en un solo sitio. */
export const RUTAS = {
  inicio: '/inicio',
  acceso: '/acceso',
  recuperarContrasena: '/recuperar-contrasena',
  // Estas tres las abre un enlace del correo: si cambian aquí, tienen que
  // cambiar también en `usuarios/servicios/correos.py` del backend.
  invitacion: '/invitacion',
  nuevaContrasena: '/nueva-contrasena',
  verificarCorreo: '/verificar-correo',

  // Las secciones del menú lateral.
  puntoDeVenta: '/punto-de-venta',
  productos: '/productos',
  categorias: '/categorias',
  proveedores: '/proveedores',
  jornadas: '/jornadas',
  cuentas: '/cuentas',
  pulseras: '/pulseras',
  pedidos: '/pedidos',
  tiendas: '/tiendas',
  cartera: '/cartera',
  clientes: '/clientes',
  pqrs: '/pqrs',
  configuracion: '/configuracion',
}

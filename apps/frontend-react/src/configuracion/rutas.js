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
  compras: '/compras',
  productos: '/productos',
  categorias: '/categorias',
  proveedores: '/proveedores',
  cartera: '/cartera',
  cuentasPorPagar: '/cuentas-por-pagar',
  registrarAbonoCompra: '/cuentas-por-pagar/:cuentaId/abono',
  clientes: '/clientes',
  pqrs: '/pqrs',
  configuracion: '/configuracion',
}

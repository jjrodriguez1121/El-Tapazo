/*
 * Datos de ejemplo del tablero, en un solo sitio.
 *
 * El tablero todavía no está conectado al backend: todo lo que enseña sale de
 * aquí y de ningún otro lado. Conectarlo es cambiar este archivo por hooks que
 * lean de la API —el resumen de ventas de `negocios`, las existencias bajo
 * mínimo de `inventario` y los pedidos de `distribucion`—; los componentes ya
 * reciben todo por props y no se enteran del cambio.
 */

export const INDICADORES = [
  { id: 'ventas', etiqueta: 'Ventas de hoy', valor: 1240000, esDinero: true, variacion: '+18%' },
  { id: 'productos', etiqueta: 'Productos en stock', valor: 720, variacion: '+24' },
  { id: 'pedidos', etiqueta: 'Pedidos pendientes', valor: 5, variacion: '2 hoy' },
  { id: 'stock-bajo', etiqueta: 'Stock bajo', valor: 6, variacion: 'revisar' },
]

export const VENTAS_DE_LA_SEMANA = {
  total: 4280000,
  dias: [
    { dia: 'Lun', total: 410000 },
    { dia: 'Mar', total: 520000 },
    { dia: 'Mié', total: 330000 },
    { dia: 'Jue', total: 640000 },
    { dia: 'Vie', total: 780000 },
    { dia: 'Sáb', total: 1050000 },
    { dia: 'Dom', total: 550000 },
  ],
}

export const PRODUCTOS_MAS_VENDIDOS = [
  {
    id: 1,
    nombre: 'Cerveza Águila 330 ml',
    sku: 'CER-001',
    categoria: 'Cervezas',
    vendidos: 186,
    precio: 5000,
  },
  {
    id: 2,
    nombre: 'Aguardiente Antioqueño 750 ml',
    sku: 'LIC-004',
    categoria: 'Licores',
    vendidos: 64,
    precio: 68000,
  },
  {
    id: 3,
    nombre: 'Cerveza Club Colombia 330 ml',
    sku: 'CER-007',
    categoria: 'Cervezas',
    vendidos: 52,
    precio: 6000,
  },
  {
    id: 4,
    nombre: 'Gaseosa Coca-Cola 1.5 L',
    sku: 'GAS-002',
    categoria: 'Gaseosas',
    vendidos: 38,
    precio: 7500,
  },
]

export const ALERTAS_DE_STOCK = [
  { id: 1, producto: 'Ron Medellín 750 ml', ubicacion: 'Bodega principal', disponible: 8 },
  { id: 2, producto: 'Cerveza Poker x24', ubicacion: 'Bodega principal', disponible: 5 },
  { id: 3, producto: 'Agua Cristal 600 ml', ubicacion: 'Barra', disponible: 3 },
  { id: 4, producto: 'Hielo en bolsa 2 kg', ubicacion: 'Barra', disponible: 0 },
  { id: 5, producto: 'Gaseosa Colombiana 1.5 L', ubicacion: 'Bodega principal', disponible: 6 },
]

export const PEDIDOS_RECIENTES = [
  { id: 1042, tienda: 'Tienda Doña Rosa', detalle: '12 cajas · Envigado', estado: 'en_ruta' },
  { id: 1041, tienda: 'Supermercado El Vecino', detalle: '30 cajas · Itagüí', estado: 'entregado' },
  { id: 1040, tienda: 'Licorera La 70', detalle: '8 cajas · Laureles', estado: 'pendiente' },
]

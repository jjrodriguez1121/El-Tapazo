/** Opciones de radicación de solicitudes PQR. */
export const TIPOS_PQR = [
  {
    id: 'queja',
    etiqueta: 'Queja',
    descripcion: 'Inconformidad con la atención o cumplimiento del servicio',
  },
  {
    id: 'reclamo',
    etiqueta: 'Reclamo',
    descripcion: 'Inconformidad directa por facturación o mercancía defectuosa/averiada',
  },
  {
    id: 'peticion',
    etiqueta: 'Petición',
    descripcion: 'Solicitud formal de información, cartera o atención',
  },
  {
    id: 'sugerencia',
    etiqueta: 'Sugerencia',
    descripcion: 'Propuesta de mejora en la logística o catálogo de productos',
  },
]

/** Motivos / Ámbitos principales de la PQR en una distribuidora. */
export const AMBITOS_PQR = [
  {
    id: 'servicio',
    etiqueta: 'Servicio',
    descripcion: 'Tiempos de entrega en ruta, atención de transportadores/asesores o facturación',
    icono: '🚚',
  },
  {
    id: 'productos',
    etiqueta: 'Productos',
    descripcion: 'Averías en transporte, fechas de vencimiento, faltantes o estado de mercancía',
    icono: '📦',
  },
]

/** Canales de recepción en la distribuidora. */
export const CANALES_RECEPCION = [
  { id: 'telefonico', etiqueta: 'Telefónico' },
  { id: 'presencial', etiqueta: 'Presencial' },
]

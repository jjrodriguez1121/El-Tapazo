/** Tipos estándar de solicitudes PQR. */
export const TIPOS_PQR = [
  { id: 'queja', etiqueta: 'Queja', descripcion: 'Inconformidad con la atención o cumplimiento del servicio' },
  { id: 'reclamo', etiqueta: 'Reclamo', descripcion: 'Inconformidad directa por facturación o mercancía defectuosa/averiada' },
  { id: 'peticion', etiqueta: 'Petición', descripcion: 'Solicitud formal de información, cartera o atención' },
  { id: 'sugerencia', etiqueta: 'Sugerencia', descripcion: 'Propuesta de mejora en la logística o catálogo de productos' },
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

/** Datos de ejemplo para una distribuidora mayorista. */
export const PQRS_DE_EJEMPLO = [
  {
    id: 'PQR-001',
    fecha: '2026-10-10T14:30:00Z',
    tipo: 'reclamo',
    ambito: 'productos',
    cliente: {
      nombre: 'Minimercado La 70 (Jorge Gómez)',
      documento: '900345678-1',
      telefono: '3104567890',
      correo: 'la70@minimercado.com',
    },
    asunto: 'Botellas quebradas en canastilla de Águila Light',
    descripcion:
      'El cliente manifiesta que al descargar el pedido en la tienda llegaron 3 unidades rotas por movimiento durante el transporte.',
    canal: 'presencial',
    estado: 'resuelta',
    respuesta: 'Se aprobó la reposición de las 3 unidades en el siguiente despacho programado.',
  },
  {
    id: 'PQR-002',
    fecha: '2026-10-11T10:15:00Z',
    tipo: 'queja',
    ambito: 'servicio',
    cliente: {
      nombre: 'Licorera El Trébol (Martha Lucía)',
      documento: '1035678901',
      telefono: '3157891234',
      correo: 'eltrebol@licorera.com',
    },
    asunto: 'Retraso en la entrega de la ruta de los jueves',
    descripcion:
      'La cliente reporta que el camión de reparto no llegó en la franja acordada de la mañana y afectó sus ventas del fin de semana.',
    canal: 'telefonico',
    estado: 'en_proceso',
    respuesta: '',
  },
  {
    id: 'PQR-003',
    fecha: '2026-10-12T16:40:00Z',
    tipo: 'sugerencia',
    ambito: 'productos',
    cliente: {
      nombre: 'Estanco El Poblado (Andrés Restrepo)',
      documento: '71987654',
      telefono: '3001234567',
      correo: 'andres@estancopoblado.com',
    },
    asunto: 'Disponibilidad de presentación en lata de Club Colombia',
    descripcion:
      'El cliente sugiere incluir en el catálogo mayorista la presentación en lata de 330 ml debido a la alta demanda en su zona.',
    canal: 'telefonico',
    estado: 'pendiente',
    respuesta: '',
  },
]

import {
  BeerSteinIcon,
  BrandyIcon,
  DropIcon,
  LightningIcon,
  MartiniIcon,
  PintGlassIcon,
} from '@phosphor-icons/react'

/** Categorías de bebidas del catálogo basadas en productos nacionales (sin descripción). */
export const CATEGORIAS_DE_EJEMPLO = [
  {
    id: 1,
    nombre: 'Cervezas',
    cantidadProductos: 13,
    Icono: BeerSteinIcon,
    productos: [
      'Águila',
      'Águila Light',
      'Águila Cero',
      'Club Colombia Dorada',
      'Club Colombia Roja',
      'Club Colombia Negra',
      'Poker',
      'Costeña',
      'Costeñita',
      'Andina',
      'Andina Light',
      '3 Cordilleras',
      'BBC',
    ],
  },
  {
    id: 2,
    nombre: 'Gaseosas',
    cantidadProductos: 12,
    Icono: PintGlassIcon,
    productos: [
      'Colombiana',
      'Manzana Postobón',
      'Uva Postobón',
      'Naranja Postobón',
      'Pepsi',
      'Pepsi Zero',
      'Coca-Cola',
      'Coca-Cola Zero',
      'Sprite',
      'Quatro',
      'Kola Roman',
      'Bretaña',
    ],
  },
  {
    id: 3,
    nombre: 'Energizantes',
    cantidadProductos: 6,
    Icono: LightningIcon,
    productos: ['Vive 100', 'Vive 100 Zero', 'Speed Max', 'Volt', 'Peak', 'Amper'],
  },
  {
    id: 4,
    nombre: 'Aguas',
    cantidadProductos: 6,
    Icono: DropIcon,
    productos: [
      'Agua Cristal',
      'Agua Cristal con Gas',
      'Agua Brisa',
      'Agua Brisa con Gas',
      'Agua Manantial',
      'Agua Hatsu',
    ],
  },
  {
    id: 5,
    nombre: 'Aguardientes',
    cantidadProductos: 7,
    Icono: MartiniIcon,
    productos: [
      'Aguardiente Antioqueño',
      'Aguardiente Antioqueño Sin Azúcar',
      'Aguardiente Amarillo de Manzanares',
      'Aguardiente Néctar',
      'Aguardiente Néctar Club Verde',
      'Aguardiente Cristal',
      'Aguardiente Tapa Roja',
    ],
  },
  {
    id: 6,
    nombre: 'Ron',
    cantidadProductos: 6,
    Icono: BrandyIcon,
    productos: [
      'Ron Medellín Añejo',
      'Ron Medellín Extra Añejo',
      'Ron Viejo de Caldas',
      'Ron Viejo de Caldas Carta de Oro',
      'Ron Viejo de Caldas Tradicional',
      'Ron Caldas',
    ],
  },
]

const PRECIOS_BASE_POR_CATEGORIA = [4500, 2500, 6500, 2000, 28000, 26000]
const STOCKS_DE_EJEMPLO = [18, 4, 0, 32, 8, 15, 2, 25]
const UBICACIONES_DE_EJEMPLO = ['Bodega A-12', 'Bodega B-04', 'Bodega C-01', 'Bodega D-08']
const PREFIJOS_SKU_POR_CATEGORIA = ['CER', 'GAS', 'ENE', 'AGU', 'AGR', 'RON']
const PROVEEDORES_POR_CATEGORIA = [
  'Bavaria S.A.',
  'Postobón S.A.',
  'Postobón S.A.',
  'Postobón S.A.',
  'Coca-Cola FEMSA',
  'Coca-Cola FEMSA',
]

/** Productos de muestra derivados de las listas ya definidas en cada categoría. */
export const PRODUCTOS_DE_EJEMPLO = CATEGORIAS_DE_EJEMPLO.flatMap((categoria, indiceCategoria) =>
  categoria.productos.map((nombre, indiceProducto) => {
    const id = categoria.id * 100 + indiceProducto + 1
    const cantidadDisponible = STOCKS_DE_EJEMPLO[(indiceCategoria + indiceProducto) % STOCKS_DE_EJEMPLO.length]
    const cantidadMinima = 5

    return {
      id,
      nombre,
      sku: `${PREFIJOS_SKU_POR_CATEGORIA[indiceCategoria]}-${String(indiceProducto + 1).padStart(3, '0')}`,
      categoria: { id: categoria.id, nombre: categoria.nombre },
      precio_evento: PRECIOS_BASE_POR_CATEGORIA[indiceCategoria] + indiceProducto * 500,
      proveedor: { razonSocial: PROVEEDORES_POR_CATEGORIA[indiceCategoria] },
      esDeEjemplo: true,
      movimientos: [
        {
          id: `${id}-mov-1`,
          tipo: 'entrada',
          titulo: 'Entrada por compra',
          fecha: '12 sep 2026',
          referencia: PROVEEDORES_POR_CATEGORIA[indiceCategoria],
          cantidad: `+${Math.max(1, Math.min(cantidadDisponible, 40))}`,
        },
        {
          id: `${id}-mov-2`,
          tipo: 'salida',
          titulo: 'Salida por venta',
          fecha: '18 sep 2026',
          referencia: `VTA-${String(indiceProducto + 1).padStart(4, '0')}`,
          cantidad: '-6',
        },
        {
          id: `${id}-mov-3`,
          tipo: 'ajuste',
          titulo: 'Ajuste de inventario',
          fecha: '20 sep 2026',
          referencia: 'Conteo físico',
          cantidad: '+2',
        },
      ],
      existencias: [
        {
          producto: { id },
          ubicacion: {
            nombre: UBICACIONES_DE_EJEMPLO[(indiceCategoria + indiceProducto) % UBICACIONES_DE_EJEMPLO.length],
          },
          cantidad_disponible: cantidadDisponible,
          esta_bajo_minimo: cantidadDisponible > 0 && cantidadDisponible <= cantidadMinima,
        },
      ],
    }
  })
)

import {
  BroomIcon,
  DropIcon,
  LeafIcon,
  LightbulbIcon,
  PackageIcon,
  RecycleIcon,
  ShieldCheckIcon,
} from '@phosphor-icons/react'

/**
 * Mensajes de concientización ambiental, seguridad y buenas prácticas operativas
 * especialmente diseñados para la bodega de una distribuidora de bebidas.
 */
export const MENSAJES_INFORMATIVOS_BODEGA = [
  {
    id: 'luces-energia',
    categoria: 'Energía',
    icono: LightbulbIcon,
    colorIcono: 'text-alerta-700',
    colorFondoIcono: 'bg-alerta-50',
    texto: 'Mantén apagadas las luces y luminarias que no necesites. Aprovecha la luz natural en pasillos.',
  },
  {
    id: 'envases-retornables',
    categoria: 'Envases',
    icono: PackageIcon,
    colorIcono: 'text-azul-600',
    colorFondoIcono: 'bg-azul-50',
    texto: 'Almacena los envases retornables en un lugar seguro, seco y clasificados en sus canastillas correspondientes.',
  },
  {
    id: 'punto-ecologico',
    categoria: 'Reciclaje',
    icono: RecycleIcon,
    colorIcono: 'text-exito-700',
    colorFondoIcono: 'bg-exito-50',
    texto: 'Separa adecuadamente el plástico vinipel (strech), cartón corrugado y zunchos en el punto ecológico.',
  },
  {
    id: 'seguridad-vidrio',
    categoria: 'Seguridad',
    icono: ShieldCheckIcon,
    colorIcono: 'text-error-700',
    colorFondoIcono: 'bg-error-50',
    texto: 'Deposita las botellas rotas con precaución en el contenedor exclusivo de vidrio para evitar accidentes.',
  },
  {
    id: 'apilamiento-estibas',
    categoria: 'Estibas',
    icono: LeafIcon,
    colorIcono: 'text-exito-700',
    colorFondoIcono: 'bg-exito-50',
    texto: 'Respeta la altura máxima de apilamiento en las estibas para prevenir caídas de producto y averías.',
  },
  {
    id: 'orden-pasillos',
    categoria: 'Orden y aseo',
    icono: BroomIcon,
    colorIcono: 'text-azul-600',
    colorFondoIcono: 'bg-azul-50',
    texto: 'Mantén los pasillos libres de cajas y estibas vacías para agilizar el alistamiento y evitar caídas.',
  },
  {
    id: 'cuidado-agua',
    categoria: 'Agua',
    icono: DropIcon,
    colorIcono: 'text-azul-600',
    colorFondoIcono: 'bg-azul-50',
    texto: 'Cierra bien las llaves en áreas de lavado y reporta cualquier fuga o goteo de inmediato.',
  },
]


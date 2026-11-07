import { PackageIcon, PhoneIcon, TruckIcon, UserIcon } from '@phosphor-icons/react'

import { formatearCantidad } from '@/utilidades/formatos'

export default function TarjetaDeProveedor({ proveedor }) {
  return (
    <article className="flex min-h-30 flex-col gap-2.5 rounded-xl border border-azul-150 bg-blanco p-3.5 transition-colors hover:border-azul-200">
      <div className="flex items-start gap-3">
        <span className="grid size-9 flex-none place-items-center rounded-lg bg-azul-50 text-azul-600">
          <TruckIcon size={19} weight="bold" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-bold text-azul-950">{proveedor.razonSocial}</h2>
          <p className="mt-0.5 text-[10px] font-medium text-azul-400">
            NIT&nbsp; {proveedor.nit || 'Pendiente'}
          </p>
        </div>
      </div>

      <div className="flex min-w-0 items-center gap-2 text-[11px] text-azul-600">
        <UserIcon size={13} className="flex-none text-azul-400" />
        <span className="truncate">{proveedor.nombreContacto || 'Contacto sin asignar'}</span>
      </div>
      <div className="flex min-w-0 items-center gap-2 text-[11px] text-azul-600">
        <PhoneIcon size={13} className="flex-none text-azul-400" />
        <span className="truncate">{proveedor.telefono || 'Teléfono sin registrar'}</span>
      </div>
      <div className="flex items-center gap-2 text-[11px] font-semibold text-exito-800">
        <PackageIcon size={13} className="flex-none" />
        {formatearCantidad(proveedor.cantidadProductos)}{' '}
        {proveedor.cantidadProductos === 1 ? 'producto' : 'productos'}
      </div>
    </article>
  )
}
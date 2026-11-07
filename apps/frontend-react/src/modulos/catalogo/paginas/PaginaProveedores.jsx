import { useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'

import ModalNuevoProveedor from '../componentes/ModalNuevoProveedor'
import TarjetaDeProveedor from '../componentes/TarjetaDeProveedor'
import { PROVEEDORES_DE_EJEMPLO } from '../utilidades/proveedoresDeEjemplo'

export default function PaginaProveedores() {
  const [proveedores, setProveedores] = useState(PROVEEDORES_DE_EJEMPLO)
  const [modalAbierto, setModalAbierto] = useState(false)

  function agregarProveedor(proveedor) {
    setProveedores((actuales) => [proveedor, ...actuales])
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold text-azul-950">Proveedores</h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            Distribuidores y casas de repuestos
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalAbierto(true)}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
        >
          <PlusIcon size={17} weight="bold" /> Nuevo proveedor
        </button>
      </header>

      <section
        aria-label="Listado de proveedores"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        {proveedores.map((proveedor) => (
          <TarjetaDeProveedor key={proveedor.id} proveedor={proveedor} />
        ))}
      </section>

      {modalAbierto && (
        <ModalNuevoProveedor
          alCerrar={() => setModalAbierto(false)}
          alCrear={agregarProveedor}
          proveedoresExistentes={proveedores}
        />
      )}
    </div>
  )
}
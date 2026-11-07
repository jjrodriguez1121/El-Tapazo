import { useState } from 'react'
import { MagnifyingGlassIcon, PlusIcon } from '@phosphor-icons/react'

import ModalNuevoCliente from '../componentes/ModalNuevoCliente'
import TarjetaDeCliente from '../componentes/TarjetaDeCliente'
import { CLIENTES_DE_EJEMPLO } from '../utilidades/clientesDeEjemplo'

export default function PaginaClientes() {
  const [clientes, setClientes] = useState(CLIENTES_DE_EJEMPLO)
  const [busqueda, setBusqueda] = useState('')
  const [modalAbierto, setModalAbierto] = useState(false)

  const textoBusqueda = busqueda.trim().toLocaleLowerCase('es-CO')
  const clientesFiltrados = clientes.filter((cliente) =>
    [cliente.nombre, cliente.telefono, cliente.documento, cliente.contacto, cliente.correo, cliente.ciudad, cliente.segmento]
      .filter(Boolean)
      .some((dato) => dato.toLocaleLowerCase('es-CO').includes(textoBusqueda))
  )

  function agregarCliente(cliente) {
    setClientes((actuales) => [cliente, ...actuales])
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold text-azul-950">Clientes</h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            Personas y establecimientos · ventas y cuentas por cobrar
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalAbierto(true)}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
        >
          <PlusIcon size={17} weight="bold" /> Nuevo cliente
        </button>
      </header>

      <label className="relative block max-w-md">
        <MagnifyingGlassIcon
          aria-hidden="true"
          size={17}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-azul-400"
        />
        <input
          type="search"
          aria-label="Buscar cliente, documento o establecimiento"
          placeholder="Buscar cliente, documento o establecimiento"
          value={busqueda}
          onChange={(evento) => setBusqueda(evento.target.value)}
          className="h-10 w-full rounded-xl border border-azul-150 bg-blanco pl-9 pr-3 text-sm text-azul-950 outline-none placeholder:text-azul-400 focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
        />
      </label>

      <section aria-label="Listado de clientes" className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {clientesFiltrados.map((cliente) => (
          <TarjetaDeCliente key={cliente.id} cliente={cliente} />
        ))}
        {!clientesFiltrados.length && (
          <p className="col-span-full rounded-xl border border-dashed border-azul-200 bg-blanco px-4 py-10 text-center text-sm text-azul-500">
            No hay clientes que coincidan con la búsqueda.
          </p>
        )}
      </section>

      {modalAbierto && (
        <ModalNuevoCliente
          alCerrar={() => setModalAbierto(false)}
          alCrear={agregarCliente}
          clientesExistentes={clientes}
        />
      )}
    </div>
  )
}
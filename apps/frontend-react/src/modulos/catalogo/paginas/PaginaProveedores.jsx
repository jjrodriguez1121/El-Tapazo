import { useEffect, useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'

import ModalNuevoProveedor from '../componentes/ModalNuevoProveedor'
import TarjetaDeProveedor from '../componentes/TarjetaDeProveedor'
import { clienteApi } from '@/librerias/clienteApi'

export default function PaginaProveedores() {
  const [proveedores, setProveedores] = useState([])
  const [modalAbierto, setModalAbierto] = useState(false)
  const [proveedorParaEditar, setProveedorParaEditar] = useState(null)
  const [error, setError] = useState('')

  async function cargarProveedores() {
    try {
      const { data } = await clienteApi.get('/catalogo/proveedores/?activo=true')
      const registros = Array.isArray(data) ? data : data.results ?? []
      setProveedores(registros.map((proveedor) => ({
        ...proveedor,
        razonSocial: proveedor.razon_social,
        nombreContacto: proveedor.nombre_contacto,
        cantidadProductos: proveedor.cantidadProductos ?? 0,
      })))
      setError('')
    } catch {
      setError('No fue posible cargar los proveedores.')
    }
  }

  useEffect(() => { cargarProveedores() }, [])

  function agregarProveedor(proveedor) {
    setProveedores((actuales) => [proveedor, ...actuales])
  }

  function guardarProveedor(proveedor) {
    if (proveedorParaEditar) {
      setProveedores((actuales) => actuales.map((actual) =>
        actual.id === proveedor.id ? proveedor : actual
      ))
    } else {
      agregarProveedor(proveedor)
    }
    setProveedorParaEditar(null)
    setModalAbierto(false)
  }

  async function eliminarProveedor(proveedor) {
    if (!window.confirm(`¿Eliminar el proveedor ${proveedor.razonSocial}?`)) return
    try {
      await clienteApi.post(`/catalogo/proveedores/${proveedor.id}/desactivacion/`)
      setProveedores((actuales) => actuales.filter((actual) => actual.id !== proveedor.id))
    } catch {
      setError('No fue posible eliminar el proveedor.')
    }
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
          onClick={() => { setProveedorParaEditar(null); setModalAbierto(true) }}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
        >
          <PlusIcon size={17} weight="bold" /> Nuevo proveedor
        </button>
      </header>

      {error && <p role="alert" className="text-sm text-error-600">{error}</p>}

      <section
        aria-label="Listado de proveedores"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        {proveedores.map((proveedor) => (
          <TarjetaDeProveedor
            key={proveedor.id}
            proveedor={proveedor}
            alEditar={(seleccionado) => { setProveedorParaEditar(seleccionado); setModalAbierto(true) }}
            alEliminar={eliminarProveedor}
          />
        ))}
      </section>

      {modalAbierto && (
        <ModalNuevoProveedor
          alCerrar={() => setModalAbierto(false)}
          alGuardar={guardarProveedor}
          proveedoresExistentes={proveedores}
          proveedorParaEditar={proveedorParaEditar}
        />
      )}
    </div>
  )
}
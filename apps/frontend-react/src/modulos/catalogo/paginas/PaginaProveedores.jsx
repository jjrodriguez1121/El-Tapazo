import { useEffect, useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'

import ModalNuevoProveedor from '../componentes/ModalNuevoProveedor'
import TarjetaDeProveedor from '../componentes/TarjetaDeProveedor'
import ConfirmacionAccion from '@/componentes/ui/ConfirmacionAccion'
import useFiltroPersistente from '@/hooks/useFiltroPersistente'
import { clienteApi } from '@/librerias/clienteApi'

export default function PaginaProveedores() {
  const [proveedores, setProveedores] = useState([])
  const [filtroEstado, setFiltroEstado] = useFiltroPersistente('proveedores.estado', 'activos')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [proveedorParaEditar, setProveedorParaEditar] = useState(null)
  const [error, setError] = useState('')
  const [proveedorParaCambiar, setProveedorParaCambiar] = useState(null)
  const [procesandoEstado, setProcesandoEstado] = useState(false)

  async function cargarProveedores() {
    try {
      const { data } = await clienteApi.get('/catalogo/proveedores/')
      const registros = Array.isArray(data) ? data : (data.results ?? [])
      setProveedores(
        registros.map((proveedor) => ({
          ...proveedor,
          razonSocial: proveedor.razon_social,
          nombreContacto: proveedor.nombre_contacto,
          cantidadProductos: proveedor.cantidad_productos ?? proveedor.cantidadProductos ?? 0,
          activo: proveedor.activo ?? true,
        }))
      )
      setError('')
    } catch {
      setError('No fue posible cargar los proveedores.')
    }
  }

  useEffect(() => {
    cargarProveedores()
  }, [])

  function agregarProveedor(proveedor) {
    setProveedores((actuales) => [proveedor, ...actuales])
  }

  function guardarProveedor(proveedor) {
    if (proveedorParaEditar) {
      setProveedores((actuales) =>
        actuales.map((actual) => (actual.id === proveedor.id ? proveedor : actual))
      )
    } else {
      agregarProveedor(proveedor)
    }
    setProveedorParaEditar(null)
    setModalAbierto(false)
  }

  async function cambiarEstadoProveedor() {
    const proveedor = proveedorParaCambiar
    if (!proveedor) return
    const activar = !proveedor.activo
    const accion = activar ? 'activacion' : 'desactivacion'
    setProcesandoEstado(true)
    setError('')
    try {
      const { data } = await clienteApi.post(`/catalogo/proveedores/${proveedor.id}/${accion}/`)
      setProveedores((actuales) =>
        actuales.map((actual) =>
          actual.id === proveedor.id
            ? { ...actual, ...data, activo: data.activo ?? activar }
            : actual
        )
      )
      setProveedorParaCambiar(null)
    } catch {
      setError(`No fue posible ${activar ? 'activar' : 'desactivar'} el proveedor.`)
      setProveedorParaCambiar(null)
    } finally {
      setProcesandoEstado(false)
    }
  }

  const proveedoresFiltrados = proveedores.filter(
    (proveedor) => filtroEstado === 'todos' || proveedor.activo === (filtroEstado === 'activos')
  )

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold text-azul-950">Proveedores</h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            Distribuidores y proveedores de productos
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setProveedorParaEditar(null)
            setModalAbierto(true)
          }}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
        >
          <PlusIcon size={17} weight="bold" /> Nuevo proveedor
        </button>
      </header>

      {error && (
        <p role="alert" className="text-sm text-error-600">
          {error}
        </p>
      )}

      <label className="flex items-center gap-2 self-start text-xs font-semibold text-azul-600">
        Estado
        <select
          aria-label="Estado de los proveedores"
          value={filtroEstado}
          onChange={(evento) => setFiltroEstado(evento.target.value)}
          className="h-9 rounded-lg border border-azul-150 bg-blanco px-3 text-xs text-azul-800 outline-none focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
        >
          <option value="activos">Activos</option>
          <option value="inactivos">Inactivos</option>
          <option value="todos">Todos</option>
        </select>
      </label>

      <section
        aria-label="Listado de proveedores"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        {proveedoresFiltrados.map((proveedor) => (
          <TarjetaDeProveedor
            key={proveedor.id}
            proveedor={proveedor}
            alEditar={(seleccionado) => {
              setProveedorParaEditar(seleccionado)
              setModalAbierto(true)
            }}
            alCambiarEstado={setProveedorParaCambiar}
          />
        ))}
        {!proveedoresFiltrados.length && (
          <p className="col-span-full rounded-xl border border-dashed border-azul-200 bg-blanco px-4 py-10 text-center text-sm text-azul-500">
            No hay proveedores en este estado.
          </p>
        )}
      </section>

      {modalAbierto && (
        <ModalNuevoProveedor
          alCerrar={() => setModalAbierto(false)}
          alGuardar={guardarProveedor}
          proveedoresExistentes={proveedores}
          proveedorParaEditar={proveedorParaEditar}
        />
      )}
      {proveedorParaCambiar && (
        <ConfirmacionAccion
          titulo={`${proveedorParaCambiar.activo ? 'Desactivar' : 'Activar'} proveedor`}
          descripcion={
            proveedorParaCambiar.activo
              ? `¿Deseas desactivar «${proveedorParaCambiar.razonSocial}»? Sus compras históricas se conservarán y podrás volver a activarlo después.`
              : `¿Deseas activar «${proveedorParaCambiar.razonSocial}» para volver a gestionarlo en el catálogo?`
          }
          textoConfirmar={
            proveedorParaCambiar.activo ? 'Desactivar proveedor' : 'Activar proveedor'
          }
          variante={proveedorParaCambiar.activo ? 'destructiva' : 'positiva'}
          procesando={procesandoEstado}
          alConfirmar={cambiarEstadoProveedor}
          alCancelar={() => setProveedorParaCambiar(null)}
        />
      )}
    </div>
  )
}

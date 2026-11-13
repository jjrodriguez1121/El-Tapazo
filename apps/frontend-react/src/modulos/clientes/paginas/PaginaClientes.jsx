import { useEffect, useState } from 'react'
import { MagnifyingGlassIcon, PlusIcon } from '@phosphor-icons/react'

import ModalNuevoCliente from '../componentes/ModalNuevoCliente'
import TarjetaDeCliente from '../componentes/TarjetaDeCliente'
import Aviso from '@/componentes/ui/Aviso'
import ConfirmacionAccion from '@/componentes/ui/ConfirmacionAccion'
import { useUsuarioDeSesion } from '@/estado/sesion'
import useFiltroPersistente from '@/hooks/useFiltroPersistente'
import { clienteApi } from '@/librerias/clienteApi'

function adaptarCliente(cliente, saldoPendienteActual = 0) {
  const esEstablecimiento = cliente.tipo_documento === 'nit'
  return {
    ...cliente,
    tipo: esEstablecimiento ? 'establecimiento' : 'persona',
    nombre: cliente.nombre_completo || `${cliente.nombre ?? ''} ${cliente.apellido ?? ''}`.trim(),
    documento: cliente.numero_documento,
    fechaNacimiento: cliente.fecha_nacimiento,
    tipoDocumento: cliente.tipo_documento,
    saldoPendiente: Number(cliente.saldo_pendiente ?? saldoPendienteActual),
    activo: cliente.activo ?? true,
  }
}

export default function PaginaClientes() {
  const usuario = useUsuarioDeSesion()
  const puedeCambiarEstado = usuario?.esAdministrador ?? false
  const [clientes, setClientes] = useState([])
  const [busqueda, setBusqueda] = useFiltroPersistente('clientes.busqueda', '')
  const [filtroEstado, setFiltroEstado] = useFiltroPersistente('clientes.estado', 'activos')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [clienteEnEdicion, setClienteEnEdicion] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [clienteParaCambiar, setClienteParaCambiar] = useState(null)
  const [procesandoEstado, setProcesandoEstado] = useState(false)

  async function cargarClientes() {
    setCargando(true)
    setError('')
    try {
      const { data } = await clienteApi.get('/clientes/')
      setClientes((data.results ?? data).map(adaptarCliente))
    } catch {
      setError('No fue posible cargar los clientes.')
    } finally {
      setCargando(false)
    }
  }

  function aDatosApi(cliente) {
    const partesNombre = cliente.nombre.trim().split(/\s+/)
    const nombre = partesNombre.shift() ?? ''
    const apellido = partesNombre.join(' ')
    const esEstablecimiento = cliente.tipoDocumento.toLowerCase() === 'nit'
    return {
      tipo_documento: cliente.tipoDocumento.toLowerCase(),
      numero_documento: cliente.documento,
      nombre: esEstablecimiento ? cliente.nombre.trim() : nombre,
      apellido: esEstablecimiento ? '' : apellido,
      fecha_nacimiento: cliente.fechaNacimiento || null,
      telefono: cliente.telefono,
      correo: cliente.correo,
      ciudad: cliente.ciudad,
      notas: clienteEnEdicion?.notas ?? '',
    }
  }

  async function guardarCliente(cliente) {
    const datos = aDatosApi(cliente)
    const { data } = clienteEnEdicion
      ? await clienteApi.put(`/clientes/${clienteEnEdicion.id}/`, datos)
      : await clienteApi.post('/clientes/', datos)
    if (clienteEnEdicion) {
      setClientes((actuales) =>
        actuales.map((actual) =>
          actual.id === data.id
            ? adaptarCliente(
                { ...data, saldo_pendiente: actual.saldoPendiente },
                actual.saldoPendiente
              )
            : actual
        )
      )
    } else {
      setClientes((actuales) => [adaptarCliente(data), ...actuales])
    }
  }

  function abrirEdicion(cliente) {
    setClienteEnEdicion(cliente)
    setModalAbierto(true)
  }

  async function cambiarEstadoCliente() {
    const cliente = clienteParaCambiar
    if (!cliente) return
    const activar = !cliente.activo
    const accion = activar ? 'activacion' : 'desactivacion'
    setProcesandoEstado(true)
    setError('')
    try {
      const { data } = await clienteApi.post(`/clientes/${cliente.id}/${accion}/`)
      setClientes((actuales) =>
        actuales.map((actual) =>
          actual.id === data.id
            ? adaptarCliente(
                { ...actual, ...data, saldo_pendiente: actual.saldoPendiente },
                actual.saldoPendiente
              )
            : actual
        )
      )
      setClienteParaCambiar(null)
    } catch (err) {
      setError(
        err.response?.data?.error?.mensaje ??
          `No fue posible ${activar ? 'activar' : 'desactivar'} el cliente.`
      )
      setClienteParaCambiar(null)
    } finally {
      setProcesandoEstado(false)
    }
  }

  useEffect(() => {
    cargarClientes()
  }, [])

  const textoBusqueda = busqueda.trim().toLocaleLowerCase('es-CO')
  const clientesFiltrados = clientes.filter(
    (cliente) =>
      (filtroEstado === 'todos' || cliente.activo === (filtroEstado === 'activos')) &&
      [cliente.nombre, cliente.telefono, cliente.documento, cliente.correo]
        .filter(Boolean)
        .some((dato) => dato.toLocaleLowerCase('es-CO').includes(textoBusqueda))
  )

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
          onClick={() => {
            setClienteEnEdicion(null)
            setModalAbierto(true)
          }}
          className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl bg-azul-950 px-4 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
        >
          <PlusIcon size={17} weight="bold" /> Nuevo cliente
        </button>
      </header>

      {error && <Aviso>{error}</Aviso>}

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

      <label className="flex items-center gap-2 self-start text-xs font-semibold text-azul-600">
        Estado
        <select
          aria-label="Estado de los clientes"
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
        aria-label="Listado de clientes"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        {clientesFiltrados.map((cliente) => (
          <TarjetaDeCliente
            key={cliente.id}
            cliente={cliente}
            alEditar={abrirEdicion}
            alCambiarEstado={setClienteParaCambiar}
            puedeCambiarEstado={puedeCambiarEstado}
          />
        ))}
        {cargando && (
          <p className="col-span-full px-4 py-10 text-center text-sm text-azul-400">
            Cargando clientes...
          </p>
        )}
        {!cargando && !clientesFiltrados.length && (
          <p className="col-span-full rounded-xl border border-dashed border-azul-200 bg-blanco px-4 py-10 text-center text-sm text-azul-500">
            No hay clientes que coincidan con la búsqueda.
          </p>
        )}
      </section>

      {modalAbierto && (
        <ModalNuevoCliente
          alCerrar={() => setModalAbierto(false)}
          alGuardar={guardarCliente}
          clienteInicial={clienteEnEdicion}
          clientesExistentes={clientes}
        />
      )}
      {clienteParaCambiar && (
        <ConfirmacionAccion
          titulo={`${clienteParaCambiar.activo ? 'Desactivar' : 'Activar'} cliente`}
          descripcion={
            clienteParaCambiar.activo
              ? `¿Deseas desactivar a «${clienteParaCambiar.nombre}»? Sus ventas y cuentas históricas se conservarán y podrás volver a activarlo después.`
              : `¿Deseas activar a «${clienteParaCambiar.nombre}» para volver a gestionarlo?`
          }
          textoConfirmar={clienteParaCambiar.activo ? 'Desactivar cliente' : 'Activar cliente'}
          variante={clienteParaCambiar.activo ? 'destructiva' : 'positiva'}
          procesando={procesandoEstado}
          alConfirmar={cambiarEstadoCliente}
          alCancelar={() => setClienteParaCambiar(null)}
        />
      )}
    </div>
  )
}

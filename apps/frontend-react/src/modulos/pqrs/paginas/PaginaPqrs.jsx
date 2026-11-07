import { useState } from 'react'
import {
  ChatCircleDotsIcon,
  CheckCircleIcon,
  ClockIcon,
  MagnifyingGlassIcon,
  PackageIcon,
} from '@phosphor-icons/react'

import FormularioPqr from '../componentes/FormularioPqr'
import TarjetaPqr from '../componentes/TarjetaPqr'
import { PQRS_DE_EJEMPLO } from '../utilidades/pqrsDeEjemplo'

/**
 * Pantalla principal del módulo de PQRs.
 * Permite radicar nuevas solicitudes solicitadas por clientes
 * y consultar el historial clasificado por Servicio o Productos.
 */
export default function PaginaPqrs() {
  const [listaPqrs, setListaPqrs] = useState(PQRS_DE_EJEMPLO)
  const [filtroAmbito, setFiltroAmbito] = useState('todos') // 'todos' | 'servicio' | 'productos'
  const [busqueda, setBusqueda] = useState('')

  function agregarPqr(nuevaPqr) {
    setListaPqrs((previas) => [nuevaPqr, ...previas])
  }

  const pqrsFiltradas = listaPqrs.filter((pqr) => {
    const coincideAmbito =
      filtroAmbito === 'todos' || pqr.ambito === filtroAmbito

    const termino = busqueda.trim().toLowerCase()
    const coincideTexto =
      !termino ||
      pqr.asunto.toLowerCase().includes(termino) ||
      pqr.descripcion.toLowerCase().includes(termino) ||
      pqr.cliente?.nombre?.toLowerCase().includes(termino) ||
      pqr.id.toLowerCase().includes(termino)

    return coincideAmbito && coincideTexto
  })

  const totalServicio = listaPqrs.filter((p) => p.ambito === 'servicio').length
  const totalProductos = listaPqrs.filter((p) => p.ambito === 'productos').length
  const totalPendientes = listaPqrs.filter((p) => p.estado === 'pendiente').length

  return (
    <div className="flex flex-col gap-6">
      {/* Encabezado */}
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-azul-50 text-azul-950">
            <ChatCircleDotsIcon size={22} weight="bold" />
          </div>
          <h1 className="text-titulo font-bold tracking-tight text-azul-950">
            PQRs
          </h1>
        </div>
        <p className="text-sm font-medium text-azul-400">
          Peticiones, quejas, reclamos y sugerencias solicitadas por clientes · Clasificadas por Servicio y Productos
        </p>
      </header>

      {/* Indicadores rápidos de conteo */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-azul-150 bg-blanco p-4">
          <span className="text-xs font-semibold text-azul-400">Total registradas</span>
          <p className="mt-1 text-2xl font-bold text-azul-950">{listaPqrs.length}</p>
        </div>
        <div className="rounded-2xl border border-azul-150 bg-blanco p-4">
          <span className="text-xs font-semibold text-azul-400">Por Servicio 🚚</span>
          <p className="mt-1 text-2xl font-bold text-azul-950">{totalServicio}</p>
        </div>
        <div className="rounded-2xl border border-azul-150 bg-blanco p-4">
          <span className="text-xs font-semibold text-azul-400">Por Productos 📦</span>
          <p className="mt-1 text-2xl font-bold text-azul-950">{totalProductos}</p>
        </div>
        <div className="rounded-2xl border border-azul-150 bg-blanco p-4">
          <span className="text-xs font-semibold text-alerta-700">Pendientes</span>
          <p className="mt-1 text-2xl font-bold text-alerta-700">{totalPendientes}</p>
        </div>
      </div>

      {/* Disposición: Formulario a la izquierda, Historial a la derecha */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.25fr_1fr] items-start">
        {/* Columna 1: Formulario para radicar */}
        <section aria-label="Sección para radicar PQR">
          <FormularioPqr alRadicar={agregarPqr} />
        </section>

        {/* Columna 2: Historial de PQRs */}
        <section
          aria-label="Historial de PQRs radicadas"
          className="flex flex-col gap-4 rounded-2xl border border-azul-150 bg-azul-50/50 p-5"
        >
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-azul-950">
                PQRs radicadas ({pqrsFiltradas.length})
              </h2>
            </div>

            {/* Buscador */}
            <div className="relative">
              <MagnifyingGlassIcon
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-azul-400"
              />
              <input
                type="search"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar por cliente, asunto o código..."
                className="h-9 w-full rounded-xl border border-azul-200 bg-blanco pl-8.5 pr-3 text-xs text-azul-950 placeholder-azul-300 outline-none focus:border-azul-600 focus:ring-2 focus:ring-azul-600/15"
              />
            </div>

            {/* Filtros rápidos por Ámbito */}
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-azul-400 font-medium">Filtrar:</span>
              <button
                type="button"
                onClick={() => setFiltroAmbito('todos')}
                className={`rounded-lg px-2.5 py-1 font-bold transition-all cursor-pointer ${
                  filtroAmbito === 'todos'
                    ? 'bg-azul-950 text-blanco'
                    : 'bg-blanco text-azul-600 border border-azul-150 hover:bg-azul-100'
                }`}
              >
                Todos
              </button>
              <button
                type="button"
                onClick={() => setFiltroAmbito('servicio')}
                className={`rounded-lg px-2.5 py-1 font-bold transition-all cursor-pointer ${
                  filtroAmbito === 'servicio'
                    ? 'bg-azul-950 text-blanco'
                    : 'bg-blanco text-azul-600 border border-azul-150 hover:bg-azul-100'
                }`}
              >
                🚚 Servicio
              </button>
              <button
                type="button"
                onClick={() => setFiltroAmbito('productos')}
                className={`rounded-lg px-2.5 py-1 font-bold transition-all cursor-pointer ${
                  filtroAmbito === 'productos'
                    ? 'bg-azul-950 text-blanco'
                    : 'bg-blanco text-azul-600 border border-azul-150 hover:bg-azul-100'
                }`}
              >
                📦 Productos
              </button>
            </div>
          </div>

          {/* Listado */}
          <div className="flex flex-col gap-3">
            {pqrsFiltradas.length === 0 ? (
              <div className="rounded-xl border border-dashed border-azul-200 bg-blanco p-6 text-center text-xs text-azul-400">
                No hay solicitudes que coincidan con la búsqueda o filtro seleccionado.
              </div>
            ) : (
              pqrsFiltradas.map((pqr) => <TarjetaPqr key={pqr.id} pqr={pqr} />)
            )}
          </div>
        </section>
      </div>
    </div>
  )
}


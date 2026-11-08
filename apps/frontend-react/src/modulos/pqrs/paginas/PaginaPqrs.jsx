import { useCallback, useEffect, useState } from 'react'
import { ChatCircleDotsIcon, MagnifyingGlassIcon } from '@phosphor-icons/react'

import { mensajeDeError } from '@/utilidades/errores'

import { crearPqr, listarPqrs, obtenerResumenPqrs, registrarSeguimientoPqr } from '../api/apiPqrs'
import FormularioPqr from '../componentes/FormularioPqr'
import TarjetaPqr from '../componentes/TarjetaPqr'

const RESUMEN_VACIO = { total: 0, servicio: 0, productos: 0, pendientes: 0 }

export default function PaginaPqrs() {
  const [listaPqrs, setListaPqrs] = useState([])
  const [resumen, setResumen] = useState(RESUMEN_VACIO)
  const [filtroAmbito, setFiltroAmbito] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)
  const [hayAnterior, setHayAnterior] = useState(false)
  const [haySiguiente, setHaySiguiente] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [pqrGuardada, setPqrGuardada] = useState('')

  const cargarDatos = useCallback(async () => {
    setCargando(true)
    setError('')
    try {
      const [respuesta, conteo] = await Promise.all([
        listarPqrs({ page: pagina, ambito: filtroAmbito, search: busqueda.trim() }),
        obtenerResumenPqrs(),
      ])
      setListaPqrs(respuesta.results ?? respuesta)
      setHayAnterior(Boolean(respuesta.previous))
      setHaySiguiente(Boolean(respuesta.next))
      setResumen(conteo)
    } catch (errorDeCarga) {
      setError(mensajeDeError(errorDeCarga))
    } finally {
      setCargando(false)
    }
  }, [pagina, filtroAmbito, busqueda])

  useEffect(() => {
    const temporizador = window.setTimeout(cargarDatos, 250)
    return () => window.clearTimeout(temporizador)
  }, [cargarDatos])

  async function radicarPqr(datos) {
    const nuevaPqr = await crearPqr(datos)
    setPqrGuardada(nuevaPqr.radicado)
    setPagina(1)
    if (pagina === 1) await cargarDatos()
    return nuevaPqr
  }

  async function agregarSeguimiento(pqrId, datos) {
    await registrarSeguimientoPqr(pqrId, datos)
    await cargarDatos()
  }

  function cambiarAmbito(ambito) {
    setFiltroAmbito(ambito)
    setPagina(1)
  }

  function cambiarBusqueda(valor) {
    setBusqueda(valor)
    setPagina(1)
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-azul-50 text-azul-950">
            <ChatCircleDotsIcon size={22} weight="bold" />
          </div>
          <h1 className="text-titulo font-bold tracking-tight text-azul-950">PQRs</h1>
        </div>
        <p className="text-sm font-medium text-azul-400">
          Registra solicitudes y consulta su gestión, respuestas y estado.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Indicador titulo="Total registradas" valor={resumen.total} />
        <Indicador titulo="Por Servicio 🚚" valor={resumen.servicio} />
        <Indicador titulo="Por Productos 📦" valor={resumen.productos} />
        <Indicador titulo="Pendientes" valor={resumen.pendientes} destacado />
      </div>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1.25fr_1fr]">
        <section aria-label="Sección para radicar PQR">
          <FormularioPqr
            alRadicar={radicarPqr}
            alLimpiarExito={() => setPqrGuardada('')}
            radicadoExitoso={pqrGuardada}
          />
        </section>

        <section
          aria-label="Historial de PQRs radicadas"
          className="flex flex-col gap-4 rounded-2xl border border-azul-150 bg-azul-50/50 p-5"
        >
          <div className="flex flex-col gap-3">
            <h2 className="text-base font-bold text-azul-950">PQRs radicadas</h2>
            <div className="relative">
              <MagnifyingGlassIcon
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-azul-400"
              />
              <input
                type="search"
                value={busqueda}
                onChange={(evento) => cambiarBusqueda(evento.target.value)}
                placeholder="Buscar por cliente, asunto o radicado..."
                aria-label="Buscar PQR"
                className="h-9 w-full rounded-xl border border-azul-200 bg-blanco pl-8.5 pr-3 text-xs text-azul-950 placeholder-azul-300 outline-none focus:border-azul-600 focus:ring-2 focus:ring-azul-600/15"
              />
            </div>
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="font-medium text-azul-400">Filtrar:</span>
              {[
                { id: '', etiqueta: 'Todos' },
                { id: 'servicio', etiqueta: '🚚 Servicio' },
                { id: 'productos', etiqueta: '📦 Productos' },
              ].map((filtro) => (
                <button
                  key={filtro.id || 'todos'}
                  type="button"
                  onClick={() => cambiarAmbito(filtro.id)}
                  aria-pressed={filtroAmbito === filtro.id}
                  className={`cursor-pointer rounded-lg px-2.5 py-1 font-bold transition-all ${
                    filtroAmbito === filtro.id
                      ? 'bg-azul-950 text-blanco'
                      : 'border border-azul-150 bg-blanco text-azul-600 hover:bg-azul-100'
                  }`}
                >
                  {filtro.etiqueta}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-700">
              {error}
            </p>
          )}
          {cargando ? (
            <p role="status" className="py-6 text-center text-sm text-azul-500">
              Cargando solicitudes...
            </p>
          ) : listaPqrs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-azul-200 bg-blanco p-6 text-center text-xs text-azul-400">
              No hay solicitudes que coincidan con la búsqueda o filtro seleccionado.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {listaPqrs.map((pqr) => (
                <TarjetaPqr key={pqr.id} pqr={pqr} alAgregarSeguimiento={agregarSeguimiento} />
              ))}
            </div>
          )}

          {(hayAnterior || haySiguiente) && (
            <div className="flex items-center justify-between border-t border-azul-150 pt-3">
              <button
                type="button"
                disabled={!hayAnterior || cargando}
                onClick={() => setPagina((actual) => actual - 1)}
                className="rounded-lg border border-azul-200 bg-blanco px-3 py-1.5 text-xs font-bold text-azul-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Anterior
              </button>
              <span className="text-xs text-azul-500">Página {pagina}</span>
              <button
                type="button"
                disabled={!haySiguiente || cargando}
                onClick={() => setPagina((actual) => actual + 1)}
                className="rounded-lg border border-azul-200 bg-blanco px-3 py-1.5 text-xs font-bold text-azul-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function Indicador({ titulo, valor, destacado = false }) {
  return (
    <div className="rounded-2xl border border-azul-150 bg-blanco p-4">
      <span className={`text-xs font-semibold ${destacado ? 'text-alerta-700' : 'text-azul-400'}`}>
        {titulo}
      </span>
      <p className={`mt-1 text-2xl font-bold ${destacado ? 'text-alerta-700' : 'text-azul-950'}`}>
        {valor}
      </p>
    </div>
  )
}

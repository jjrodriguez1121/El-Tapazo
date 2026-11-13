import { useRef, useState } from 'react'
import { CheckIcon, FilePdfIcon, MagnifyingGlassIcon, PlusIcon, XIcon } from '@phosphor-icons/react'

import { mensajeDeError } from '@/utilidades/errores'
import { formatearPesos } from '@/utilidades/formatos'
import { buscarCoincidenciasFacturaPdf } from '../api/apiCompras'

const NUEVO = 'nuevo'

// Lo que el buscador dice de cada renglón de la factura.
const ESTADOS = {
  COINCIDE: { texto: 'Coincide', tono: 'bg-exito-50 text-exito-700' },
  PROBABLE: { texto: 'Revisar', tono: 'bg-alerta-50 text-alerta-700' },
  NUEVO: { texto: 'Nuevo', tono: 'bg-azul-75 text-azul-600' },
}

function TonoDeSimilitud({ valor }) {
  const porcentaje = Math.round(valor * 100)
  const tono =
    porcentaje >= 80
      ? 'bg-exito-50 text-exito-700'
      : porcentaje >= 60
        ? 'bg-alerta-50 text-alerta-700'
        : 'bg-error-50 text-error-700'
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${tono}`}>{porcentaje}%</span>
  )
}

/**
 * Buscador de coincidencias: sube la factura del proveedor en PDF, el backend
 * lee sus renglones (cantidad × unitario = total) y busca cada uno en el
 * catálogo por código y por parecido del nombre. No usa IA. Con "Agregar" la línea pasa a la compra que se está
 * armando. El análisis queda abierto después de registrar, así que una misma
 * factura puede repartirse en varias compras; las líneas ya agregadas quedan
 * marcadas.
 */
export default function ImportarFacturaPdf({
  alAgregarLinea,
  alUsarEncabezado,
  proveedorActualId,
}) {
  const [archivo, setArchivo] = useState(null)
  const [analizando, setAnalizando] = useState(false)
  const [error, setError] = useState('')
  const [analisis, setAnalisis] = useState(null)
  const [elecciones, setElecciones] = useState({})
  const [agregadas, setAgregadas] = useState({})
  const entrada = useRef(null)

  async function analizar() {
    if (!archivo) return
    setAnalizando(true)
    setError('')
    try {
      const resultado = await buscarCoincidenciasFacturaPdf(archivo)
      setAnalisis(resultado)
      setAgregadas({})
      setElecciones(
        Object.fromEntries(
          resultado.lineas.map((linea) => [
            linea.indice,
            linea.candidatos[0] ? String(linea.candidatos[0].id) : NUEVO,
          ])
        )
      )
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setAnalizando(false)
    }
  }

  function descartar() {
    setAnalisis(null)
    setArchivo(null)
    setError('')
    if (entrada.current) entrada.current.value = ''
  }

  function agregar(linea) {
    const eleccion = elecciones[linea.indice]
    const producto = linea.candidatos.find((candidato) => String(candidato.id) === eleccion)
    alAgregarLinea({ linea, producto: producto ?? null })
    setAgregadas((actuales) => ({ ...actuales, [linea.indice]: (actuales[linea.indice] ?? 0) + 1 }))
  }

  const pendientes = analisis?.lineas.filter((linea) => !agregadas[linea.indice]) ?? []

  return (
    <section className="rounded-xl border border-dashed border-azul-300 bg-azul-50/60 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="grid size-10 place-items-center rounded-lg bg-blanco text-azul-700">
          <FilePdfIcon size={22} weight="duotone" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold text-azul-950">Importar factura PDF</h3>
          <p className="text-xs text-azul-500">
            Busca los productos de la factura del proveedor en tu catálogo.
          </p>
        </div>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-azul-200 bg-blanco px-3 py-2 text-xs font-bold text-azul-700 hover:bg-azul-75">
          {archivo ? archivo.name : 'Elegir PDF'}
          <input
            ref={entrada}
            type="file"
            accept="application/pdf,.pdf"
            aria-label="Factura en PDF"
            className="sr-only"
            onChange={(evento) => {
              setArchivo(evento.target.files?.[0] ?? null)
              setError('')
            }}
          />
        </label>
        <button
          type="button"
          onClick={analizar}
          disabled={!archivo || analizando}
          className="inline-flex items-center gap-2 rounded-lg bg-azul-950 px-3 py-2 text-xs font-bold text-blanco hover:bg-azul-800 disabled:opacity-50"
        >
          <MagnifyingGlassIcon size={15} weight="bold" />
          {analizando ? 'Buscando…' : 'Buscar coincidencias'}
        </button>
      </div>

      {error && <p className="mt-3 text-xs font-semibold text-error-700">{error}</p>}

      {analisis && (
        <div className="mt-4 flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg bg-blanco px-3 py-2 text-xs text-azul-600">
            <span>
              Factura: <strong className="text-azul-950">{analisis.numero_factura || 'N/D'}</strong>
            </span>
            <span>
              Proveedor:{' '}
              <strong className="text-azul-950">
                {analisis.proveedor?.razon_social ??
                  (analisis.proveedor_detectado.nombre
                    ? `${analisis.proveedor_detectado.nombre} (no registrado)`
                    : 'N/D')}
              </strong>
            </span>
            {(analisis.numero_factura || analisis.proveedor) && (
              <button
                type="button"
                onClick={() =>
                  alUsarEncabezado({
                    numeroFactura: analisis.numero_factura,
                    proveedorId: analisis.proveedor ? String(analisis.proveedor.id) : '',
                  })
                }
                className="rounded-md border border-azul-200 px-2 py-1 font-bold text-azul-700 hover:bg-azul-75"
              >
                Usar en la compra
              </button>
            )}
            <button
              type="button"
              onClick={descartar}
              aria-label="Cerrar el análisis"
              className="ml-auto grid size-7 place-items-center rounded-md text-azul-500 hover:bg-azul-75"
            >
              <XIcon size={15} />
            </button>
          </div>

          {analisis.proveedor &&
            proveedorActualId &&
            String(analisis.proveedor.id) !== String(proveedorActualId) && (
              <p className="text-xs font-semibold text-alerta-700">
                El proveedor de la factura no es el seleccionado en la compra.
              </p>
            )}

          {!analisis.lineas.length ? (
            <p className="text-xs text-azul-500">No se encontraron productos en la factura.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-azul-150 bg-blanco">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-azul-50 text-xs uppercase text-azul-500">
                  <tr>
                    <th className="px-3 py-2">En la factura</th>
                    <th className="px-3 py-2 text-center">Cant.</th>
                    <th className="px-3 py-2 text-right">Costo unit.</th>
                    <th className="px-3 py-2">Producto del catálogo</th>
                    <th className="px-3 py-2 text-center">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {analisis.lineas.map((linea) => {
                    const eleccion = elecciones[linea.indice]
                    const elegido = linea.candidatos.find((c) => String(c.id) === eleccion)
                    const vecesAgregada = agregadas[linea.indice] ?? 0
                    return (
                      <tr key={linea.indice} className="border-t border-azul-100 align-top">
                        <td className="px-3 py-2">
                          <p className="font-semibold text-azul-950">{linea.descripcion}</p>
                          {ESTADOS[linea.estado] && (
                            <span
                              className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-bold ${ESTADOS[linea.estado].tono}`}
                            >
                              {ESTADOS[linea.estado].texto}
                            </span>
                          )}
                          {linea.codigo && (
                            <p className="text-[11px] text-azul-400">Ref. {linea.codigo}</p>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center">{linea.cantidad}</td>
                        <td className="px-3 py-2 text-right">
                          {formatearPesos(Number(linea.costo_unitario))}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <select
                              aria-label={`Producto para ${linea.descripcion}`}
                              value={eleccion}
                              onChange={(evento) =>
                                setElecciones((actuales) => ({
                                  ...actuales,
                                  [linea.indice]: evento.target.value,
                                }))
                              }
                              className="h-8 min-w-0 flex-1 rounded-lg border border-azul-200 px-2 text-xs"
                            >
                              {linea.candidatos.map((candidato) => (
                                <option key={candidato.id} value={candidato.id}>
                                  {candidato.sku} · {candidato.nombre} (stock{' '}
                                  {Number(candidato.stock)})
                                </option>
                              ))}
                              <option value={NUEVO}>➕ Crear como producto nuevo</option>
                            </select>
                            {elegido ? (
                              <TonoDeSimilitud valor={elegido.similitud} />
                            ) : (
                              <span className="rounded-full bg-azul-75 px-2 py-0.5 text-[11px] font-bold text-azul-600">
                                {linea.candidatos.length ? 'Nuevo' : 'Sin coincidencias'}
                              </span>
                            )}
                          </div>
                          {elegido && Number(elegido.costo) > 0 && (
                            <p className="mt-1 text-[11px] text-azul-400">
                              Costo actual {formatearPesos(Number(elegido.costo))}
                            </p>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            type="button"
                            onClick={() => agregar(linea)}
                            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold ${
                              vecesAgregada
                                ? 'border border-exito-700/25 bg-exito-50 text-exito-700'
                                : 'bg-azul-950 text-blanco hover:bg-azul-800'
                            }`}
                          >
                            {vecesAgregada ? <CheckIcon size={14} /> : <PlusIcon size={14} />}
                            {vecesAgregada ? 'Agregada' : 'Agregar'}
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {pendientes.length > 1 && (
            <button
              type="button"
              onClick={() => pendientes.forEach(agregar)}
              className="self-start rounded-lg border border-azul-200 bg-blanco px-3 py-2 text-xs font-bold text-azul-700 hover:bg-azul-75"
            >
              Agregar las {pendientes.length} pendientes
            </button>
          )}
        </div>
      )}
    </section>
  )
}

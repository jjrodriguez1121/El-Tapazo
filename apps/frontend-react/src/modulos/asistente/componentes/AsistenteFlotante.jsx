import { Fragment, useEffect, useRef, useState } from 'react'
import { ChatCircleDotsIcon, PaperPlaneRightIcon, TrashIcon, XIcon } from '@phosphor-icons/react'

import { mensajeDeError } from '@/utilidades/errores'
import { conversarConAsistente } from '../api/apiAsistente'

const TAMANO_BURBUJA = 56
const MARGEN = 12
const ANCHO_PANEL = 360
const ALTO_PANEL = 480
// Si el puntero se mueve menos que esto, fue un clic y no un arrastre.
const UMBRAL_DE_ARRASTRE = 5
const CLAVE_POSICION = 'el-tapaso:asistente-posicion'

const SALUDO = {
  rol: 'asistente',
  contenido:
    'Hola, soy el asistente de El Tapaso. Pregúntame por productos, precios o qué está por agotarse.',
}

const SUGERENCIAS = ['¿Qué productos están agotados?', '¿Cuánto cuesta la cerveza?']

function limitar(valor, minimo, maximo) {
  return Math.min(Math.max(valor, minimo), Math.max(minimo, maximo))
}

function posicionDentroDeLaVentana({ x, y }) {
  return {
    x: limitar(x, MARGEN, window.innerWidth - TAMANO_BURBUJA - MARGEN),
    y: limitar(y, MARGEN, window.innerHeight - TAMANO_BURBUJA - MARGEN),
  }
}

function posicionInicial() {
  try {
    const guardada = JSON.parse(localStorage.getItem(CLAVE_POSICION))
    if (Number.isFinite(guardada?.x) && Number.isFinite(guardada?.y)) {
      return posicionDentroDeLaVentana(guardada)
    }
  } catch {
    // Almacenamiento bloqueado o dato dañado: se usa la esquina.
  }
  return {
    x: window.innerWidth - TAMANO_BURBUJA - 24,
    y: window.innerHeight - TAMANO_BURBUJA - 24,
  }
}

/** Pinta `**negrita**` y saltos de línea sin interpretar HTML. */
function TextoDelMensaje({ texto }) {
  return texto.split('\n').map((renglon, i) => (
    <Fragment key={i}>
      {i > 0 && <br />}
      {renglon
        .split(/(\*\*[^*]+\*\*)/g)
        .map((parte, j) =>
          parte.startsWith('**') && parte.endsWith('**') && parte.length > 4 ? (
            <strong key={j}>{parte.slice(2, -2)}</strong>
          ) : (
            parte
          )
        )}
    </Fragment>
  ))
}

/**
 * Burbuja flotante con el chat de IA. Se arrastra a cualquier punto de la
 * pantalla y recuerda dónde se dejó. El asistente responde con el catálogo y
 * el stock del negocio de quien está en sesión.
 */
export default function AsistenteFlotante() {
  const [posicion, setPosicion] = useState(posicionInicial)
  const [abierto, setAbierto] = useState(false)
  const [mensajes, setMensajes] = useState([SALUDO])
  const [borrador, setBorrador] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const arrastre = useRef(null)
  const finDeLaLista = useRef(null)
  const campo = useRef(null)

  useEffect(() => {
    const reacomodar = () => setPosicion((actual) => posicionDentroDeLaVentana(actual))
    window.addEventListener('resize', reacomodar)
    return () => window.removeEventListener('resize', reacomodar)
  }, [])

  useEffect(() => {
    finDeLaLista.current?.scrollIntoView({ block: 'end' })
  }, [mensajes, enviando, abierto])

  useEffect(() => {
    if (abierto) campo.current?.focus()
  }, [abierto])

  useEffect(() => {
    if (!abierto) return undefined
    const cerrarConEsc = (evento) => {
      if (evento.key === 'Escape') setAbierto(false)
    }
    document.addEventListener('keydown', cerrarConEsc)
    return () => document.removeEventListener('keydown', cerrarConEsc)
  }, [abierto])

  function alPresionar(evento) {
    if (evento.button !== 0) return
    evento.currentTarget.setPointerCapture(evento.pointerId)
    arrastre.current = {
      inicioX: evento.clientX,
      inicioY: evento.clientY,
      origen: posicion,
      movido: false,
    }
  }

  function alMover(evento) {
    const datos = arrastre.current
    if (!datos) return
    const dx = evento.clientX - datos.inicioX
    const dy = evento.clientY - datos.inicioY
    if (!datos.movido && Math.hypot(dx, dy) < UMBRAL_DE_ARRASTRE) return
    datos.movido = true
    datos.ultima = posicionDentroDeLaVentana({ x: datos.origen.x + dx, y: datos.origen.y + dy })
    setPosicion(datos.ultima)
  }

  function alSoltar() {
    const datos = arrastre.current
    arrastre.current = null
    if (!datos) return
    if (!datos.movido) {
      setAbierto((actual) => !actual)
      return
    }
    try {
      localStorage.setItem(CLAVE_POSICION, JSON.stringify(datos.ultima))
    } catch {
      // Sin almacenamiento la burbuja vuelve a la esquina al recargar.
    }
  }

  async function enviar(texto) {
    const contenido = texto.trim()
    if (!contenido || enviando) return
    const conversacion = [...mensajes, { rol: 'usuario', contenido }]
    setMensajes(conversacion)
    setBorrador('')
    setError('')
    setEnviando(true)
    try {
      // El saludo es local: no se le manda al modelo.
      const respuesta = await conversarConAsistente(conversacion.filter((m) => m !== SALUDO))
      setMensajes((actuales) => [...actuales, { rol: 'asistente', contenido: respuesta }])
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setEnviando(false)
    }
  }

  // El panel se abre hacia donde haya espacio: arriba o abajo, izquierda o derecha.
  const anchoPanel = Math.min(ANCHO_PANEL, window.innerWidth - MARGEN * 2)
  const altoPanel = Math.min(ALTO_PANEL, window.innerHeight - TAMANO_BURBUJA - MARGEN * 4)
  const panelIzquierda = limitar(
    posicion.x + TAMANO_BURBUJA - anchoPanel,
    MARGEN,
    window.innerWidth - anchoPanel - MARGEN
  )
  const hayEspacioArriba = posicion.y - altoPanel - MARGEN >= MARGEN
  const panelArriba = hayEspacioArriba
    ? posicion.y - altoPanel - MARGEN
    : limitar(posicion.y + TAMANO_BURBUJA + MARGEN, MARGEN, window.innerHeight - altoPanel - MARGEN)

  return (
    <>
      {abierto && (
        <section
          role="dialog"
          aria-label="Asistente con IA"
          style={{ left: panelIzquierda, top: panelArriba, width: anchoPanel, height: altoPanel }}
          className="fixed z-[55] flex flex-col overflow-hidden rounded-2xl border border-azul-150 bg-blanco shadow-marco"
        >
          <header className="flex items-center gap-2 bg-azul-950 px-4 py-3 text-blanco">
            <ChatCircleDotsIcon size={20} weight="fill" />
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-bold">Asistente</h2>
              <p className="text-[11px] text-azul-300">Conoce tus productos, precios y stock</p>
            </div>
            <button
              type="button"
              aria-label="Borrar la conversación"
              title="Borrar la conversación"
              onClick={() => {
                setMensajes([SALUDO])
                setError('')
              }}
              className="grid size-8 place-items-center rounded-lg hover:bg-azul-800"
            >
              <TrashIcon size={17} />
            </button>
            <button
              type="button"
              aria-label="Cerrar el asistente"
              onClick={() => setAbierto(false)}
              className="grid size-8 place-items-center rounded-lg hover:bg-azul-800"
            >
              <XIcon size={17} />
            </button>
          </header>

          <ol
            aria-live="polite"
            className="flex flex-1 flex-col gap-2.5 overflow-y-auto bg-azul-50 p-3"
          >
            {mensajes.map((mensaje, indice) => (
              <li
                key={indice}
                className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                  mensaje.rol === 'usuario'
                    ? 'self-end rounded-br-md bg-azul-950 text-blanco'
                    : 'self-start rounded-bl-md border border-azul-150 bg-blanco text-azul-950'
                }`}
              >
                <TextoDelMensaje texto={mensaje.contenido} />
              </li>
            ))}
            {enviando && (
              <li className="self-start rounded-2xl rounded-bl-md border border-azul-150 bg-blanco px-3.5 py-2.5 text-sm text-azul-400">
                Pensando…
              </li>
            )}
            {mensajes.length === 1 && !enviando && (
              <li className="flex flex-wrap gap-2 pt-1">
                {SUGERENCIAS.map((sugerencia) => (
                  <button
                    key={sugerencia}
                    type="button"
                    onClick={() => enviar(sugerencia)}
                    className="rounded-full border border-azul-200 bg-blanco px-3 py-1.5 text-xs font-semibold text-azul-700 hover:bg-azul-75"
                  >
                    {sugerencia}
                  </button>
                ))}
              </li>
            )}
            <li ref={finDeLaLista} aria-hidden="true" />
          </ol>

          {error && (
            <p
              role="alert"
              className="border-t border-error-200 bg-error-50 px-3 py-2 text-xs font-semibold text-error-700"
            >
              {error}
            </p>
          )}

          <form
            onSubmit={(evento) => {
              evento.preventDefault()
              enviar(borrador)
            }}
            className="flex items-end gap-2 border-t border-azul-150 p-2.5"
          >
            <textarea
              ref={campo}
              rows={1}
              maxLength={2000}
              value={borrador}
              placeholder="Escribe tu pregunta…"
              aria-label="Mensaje para el asistente"
              onChange={(evento) => setBorrador(evento.target.value)}
              onKeyDown={(evento) => {
                if (evento.key === 'Enter' && !evento.shiftKey) {
                  evento.preventDefault()
                  enviar(borrador)
                }
              }}
              className="max-h-28 min-h-10 flex-1 resize-none rounded-xl border border-azul-200 px-3 py-2 text-sm focus:border-azul-600 focus:outline-none"
            />
            <button
              type="submit"
              aria-label="Enviar"
              disabled={enviando || !borrador.trim()}
              className="grid size-10 flex-none place-items-center rounded-xl bg-azul-950 text-blanco hover:bg-azul-800 disabled:opacity-40"
            >
              <PaperPlaneRightIcon size={18} weight="fill" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        aria-label={abierto ? 'Cerrar el asistente' : 'Abrir el asistente con IA'}
        aria-expanded={abierto}
        title="Asistente con IA (arrástrame)"
        onPointerDown={alPresionar}
        onPointerMove={alMover}
        onPointerUp={alSoltar}
        onPointerCancel={() => {
          arrastre.current = null
        }}
        onKeyDown={(evento) => {
          if (evento.key === 'Enter' || evento.key === ' ') {
            evento.preventDefault()
            setAbierto((actual) => !actual)
          }
        }}
        style={{ left: posicion.x, top: posicion.y, width: TAMANO_BURBUJA, height: TAMANO_BURBUJA }}
        className="fixed z-[56] grid cursor-grab touch-none place-items-center rounded-full bg-azul-950 text-blanco shadow-marco transition-colors select-none hover:bg-azul-800 active:cursor-grabbing"
      >
        {abierto ? (
          <XIcon size={24} weight="bold" />
        ) : (
          <ChatCircleDotsIcon size={28} weight="fill" />
        )}
      </button>
    </>
  )
}

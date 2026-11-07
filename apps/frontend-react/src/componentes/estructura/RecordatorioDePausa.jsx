import { useEffect, useRef, useState } from 'react'
import { EyeIcon, PersonSimpleTaiChiIcon } from '@phosphor-icons/react'

const INTERVALO_PREDETERMINADO_MS = 60 * 60 * 1000
const APLAZAMIENTO_PREDETERMINADO_MS = 10 * 60 * 1000
const INACTIVIDAD_QUE_REINICIA_MS = 5 * 60 * 1000
// Da margen al temporizador del navegador: una pausa muy corta entre acciones
// no debe impedir que aparezca el recordatorio al cumplirse el intervalo.
const ACTIVIDAD_RECIENTE_MS = 90 * 1000
const SEGUNDOS_DE_LECTURA = 5

const MENSAJES_DE_PAUSA = [
  {
    titulo: 'Descansa la vista',
    recomendacion: 'Regla 20-20-20',
    detalle: 'Mira a lo lejos durante 20 segundos. Esto ayuda a relajar el esfuerzo visual de la pantalla.',
  },
  {
    titulo: 'Revisa tu postura',
    recomendacion: 'Cuello y hombros',
    detalle: 'Relaja los hombros y mueve suavemente el cuello de un lado a otro, sin hacer movimientos bruscos.',
  },
  {
    titulo: 'Activa el cuerpo',
    recomendacion: 'Muévete durante 1 minuto',
    detalle: 'Ponte de pie, estira la espalda y camina unos pasos antes de continuar con tus actividades.',
  },
  {
    titulo: 'Toma un respiro',
    recomendacion: 'Respira e hidrátate',
    detalle: 'Respira profundamente varias veces y toma agua si la tienes a tu alcance.',
  },
]

function hayCampoEnEdicion() {
  const elementoActivo = document.activeElement
  return elementoActivo instanceof HTMLElement && elementoActivo.matches(
    'input, textarea, select, [contenteditable="true"]'
  )
}

/**
 * Propone una pausa durante una sesión de actividad continuada. No aparece
 * mientras hay un campo en edición: se muestra en la siguiente interacción
 * segura para no interrumpir el registro de datos.
 */
export default function RecordatorioDePausa({
  intervaloMs = INTERVALO_PREDETERMINADO_MS,
  aplazamientoMs = APLAZAMIENTO_PREDETERMINADO_MS,
}) {
  const [visible, setVisible] = useState(false)
  const [indiceMensaje, setIndiceMensaje] = useState(-1)
  const [segundosParaContinuar, setSegundosParaContinuar] = useState(SEGUNDOS_DE_LECTURA)
  const tituloRef = useRef(null)
  const dialogoRef = useRef(null)
  const inicioDeActividadRef = useRef(null)
  const ultimaActividadRef = useRef(null)
  const proximaPausaRef = useRef(null)

  function reiniciarConteo(desde = Date.now()) {
    inicioDeActividadRef.current = desde
    ultimaActividadRef.current = desde
    proximaPausaRef.current = desde + intervaloMs
  }

  function puedeMostrarPausa(ahora = Date.now()) {
    return (
      !visible &&
      inicioDeActividadRef.current !== null &&
      proximaPausaRef.current !== null &&
      ahora >= proximaPausaRef.current &&
      ahora - ultimaActividadRef.current <= ACTIVIDAD_RECIENTE_MS &&
      document.visibilityState === 'visible' &&
      !hayCampoEnEdicion()
    )
  }

  useEffect(() => {
    // Al entrar al panel comienza una sesión de actividad. Los eventos posteriores
    // la mantienen viva; si pasan cinco minutos sin actividad, se reinicia.
    if (inicioDeActividadRef.current === null) reiniciarConteo()

    function mostrarSiCorresponde() {
      if (puedeMostrarPausa()) {
        setIndiceMensaje((indice) => (indice + 1) % MENSAJES_DE_PAUSA.length)
        setVisible(true)
      }
    }

    function registrarActividad() {
      const ahora = Date.now()
      if (
        inicioDeActividadRef.current === null ||
        ahora - ultimaActividadRef.current > INACTIVIDAD_QUE_REINICIA_MS
      ) {
        reiniciarConteo(ahora)
        return
      }

      ultimaActividadRef.current = ahora
      mostrarSiCorresponde()
    }

    const verificador = window.setInterval(mostrarSiCorresponde, 30000)
    window.addEventListener('pointerdown', registrarActividad)
    window.addEventListener('keydown', registrarActividad)
    window.addEventListener('touchstart', registrarActividad)

    return () => {
      window.clearInterval(verificador)
      window.removeEventListener('pointerdown', registrarActividad)
      window.removeEventListener('keydown', registrarActividad)
      window.removeEventListener('touchstart', registrarActividad)
    }
  }, [visible, intervaloMs])

  useEffect(() => {
    if (!visible) return undefined

    tituloRef.current?.focus()
    setSegundosParaContinuar(SEGUNDOS_DE_LECTURA)
    const temporizador = window.setInterval(() => {
      setSegundosParaContinuar((segundos) => Math.max(0, segundos - 1))
    }, 1000)
    return () => window.clearInterval(temporizador)
  }, [visible])

  useEffect(() => {
    if (!visible) return undefined

    function mantenerElFoco(evento) {
      if (evento.key === 'Escape') evento.preventDefault()
      if (evento.key !== 'Tab') return

      const elementos = dialogoRef.current?.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
      )
      if (!elementos?.length) return

      const primero = elementos[0]
      const ultimo = elementos[elementos.length - 1]
      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault()
        ultimo.focus()
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault()
        primero.focus()
      }
    }

    document.addEventListener('keydown', mantenerElFoco)
    return () => document.removeEventListener('keydown', mantenerElFoco)
  }, [visible])

  function iniciarPausa() {
    reiniciarConteo()
    setVisible(false)
  }

  function aplazarPausa() {
    const ahora = Date.now()
    inicioDeActividadRef.current = ahora
    ultimaActividadRef.current = ahora
    proximaPausaRef.current = ahora + aplazamientoMs
    setVisible(false)
  }

  if (!visible) return null

  const mensaje = MENSAJES_DE_PAUSA[indiceMensaje] ?? MENSAJES_DE_PAUSA[0]

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center bg-azul-950/55 p-4">
      <section
        ref={dialogoRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-recordatorio-pausa"
        aria-describedby="descripcion-recordatorio-pausa"
        className="w-full max-w-md rounded-2xl border border-azul-150 bg-blanco p-6 shadow-xl sm:p-7"
      >
        <div className="flex size-12 items-center justify-center rounded-2xl bg-azul-50 text-azul-950" aria-hidden="true">
          <EyeIcon size={27} weight="duotone" />
        </div>

        <h2
          id="titulo-recordatorio-pausa"
          ref={tituloRef}
          tabIndex="-1"
          className="mt-5 text-titulo-chico font-bold text-azul-950 outline-none"
        >
          Es momento de una pausa activa
        </h2>
        <p id="descripcion-recordatorio-pausa" className="mt-2 text-sm leading-6 text-azul-600">
          Has completado un periodo de actividad continua. {mensaje.detalle}
        </p>

        <div className="mt-5 rounded-xl border border-azul-150 bg-azul-50 p-4">
          <div className="flex gap-3">
            <PersonSimpleTaiChiIcon size={23} weight="duotone" className="mt-0.5 flex-none text-azul-600" aria-hidden="true" />
            <div className="text-sm leading-5 text-azul-600">
              <p className="font-bold text-azul-950">{mensaje.titulo}</p>
              <p className="mt-1">{mensaje.recomendacion}</p>
            </div>
          </div>
        </div>

        <footer className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={aplazarPausa}
            className="rounded-xl px-4 py-3 text-sm font-bold text-azul-600 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-400"
          >
            Recordar en 10 min
          </button>
          <button
            type="button"
            onClick={iniciarPausa}
            disabled={segundosParaContinuar > 0}
            className="rounded-xl bg-azul-950 px-4 py-3 text-sm font-bold text-blanco transition-colors hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-400 disabled:cursor-not-allowed disabled:bg-azul-600"
          >
            {segundosParaContinuar > 0
              ? `Continuar en ${segundosParaContinuar} s`
              : 'Tomar mi pausa'}
          </button>
        </footer>
      </section>
    </div>
  )
}

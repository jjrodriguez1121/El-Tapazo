import { useId, useState } from 'react'
import { CheckIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import {
  validarCorreoOpcional,
  validarDocumento,
  validarFechaNacimiento,
  validarObligatorio,
  validarTelefono,
} from '@/utilidades/validaciones'

function CampoCliente({ etiqueta, id, error = '', className = '', ...props }) {
  return (
    <div className={`flex min-w-0 flex-col gap-1.5 ${className}`}>
      <label htmlFor={id} className="text-xs font-semibold text-azul-600">
        {etiqueta}
      </label>
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        className="h-10 w-full rounded-lg border border-azul-200 bg-blanco px-3 text-sm text-azul-950 outline-none placeholder:text-azul-300 focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
        {...props}
      />
      {error && <p id={`${id}-error`} className="text-[11px] font-semibold text-error-700">{error}</p>}
    </div>
  )
}

export default function ModalNuevoCliente({ alCerrar, alCrear, clientesExistentes = [] }) {
  const id = useId()
  const [datos, setDatos] = useState({
    tipo: 'persona',
    nombre: '',
    telefono: '',
    tipoDocumento: 'cedula',
    documento: '',
    fechaNacimiento: '',
    correo: '',
    ciudad: '',
    contacto: '',
    segmento: 'tienda',
  })
  const [errores, setErrores] = useState({})
  const esEstablecimiento = datos.tipo === 'establecimiento'

  function cambiar(campo, valor) {
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))
    setErrores((actuales) => ({ ...actuales, [campo]: '' }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const nombre = datos.nombre.trim()
    const telefono = datos.telefono.trim()
    const documento = datos.documento.trim()
    const nuevosErrores = {
      nombre: validarObligatorio(nombre, 'Escribe el nombre del cliente.'),
      telefono: validarTelefono(telefono),
      documento: validarDocumento(documento, esEstablecimiento ? 'El NIT' : 'El documento'),
      fechaNacimiento: esEstablecimiento ? '' : validarFechaNacimiento(datos.fechaNacimiento),
      correo: validarCorreoOpcional(datos.correo),
    }
    const documentoNormalizado = documento.replace(/[^a-z\d]/gi, '').toUpperCase()
    const tipoDocumentoNormalizado = (tipo) =>
      String(tipo ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[\s_]/g, '')
    const tipoDocumentoActual = esEstablecimiento ? 'nit' : datos.tipoDocumento
    const documentoDuplicado = clientesExistentes.some(
      (cliente) =>
        cliente.tipo === datos.tipo &&
        tipoDocumentoNormalizado(
          cliente.tipo === 'establecimiento' ? 'nit' : cliente.tipoDocumento ?? 'cedula'
        ) === tipoDocumentoNormalizado(tipoDocumentoActual) &&
        cliente.documento.replace(/[^a-z\d]/gi, '').toUpperCase() === documentoNormalizado
    )
    if (!nuevosErrores.documento && documentoDuplicado) {
      nuevosErrores.documento = 'Ya existe un cliente con ese documento o NIT.'
    }

    setErrores(nuevosErrores)
    if (Object.values(nuevosErrores).some(Boolean)) return

    alCrear({
      id: `cliente-local-${Date.now()}`,
      tipo: datos.tipo,
      nombre,
      telefono,
      tipoDocumento: esEstablecimiento ? 'NIT' : datos.tipoDocumento,
      documento,
      fechaNacimiento: esEstablecimiento ? '' : datos.fechaNacimiento,
      correo: datos.correo.trim(),
      ciudad: datos.ciudad.trim(),
      contacto: esEstablecimiento ? datos.contacto.trim() : '',
      segmento: esEstablecimiento ? datos.segmento : '',
      saldoPendiente: 0,
    })
    alCerrar()
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-azul-950/45 px-3 py-6 sm:px-6">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-titulo`}
        className="mx-auto my-4 w-full max-w-2xl rounded-xl border border-azul-150 bg-blanco p-5 shadow-xl sm:p-6"
      >
        <header className="mb-5">
          <h2 id={`${id}-titulo`} className="text-lg font-bold text-azul-950">Nuevo cliente</h2>
          <p className="mt-1 text-xs font-medium text-azul-400">
            Registra una persona o un establecimiento.
          </p>
        </header>

        <form onSubmit={enviar} noValidate className="flex flex-col gap-4">
          <fieldset>
            <legend className="mb-1.5 text-xs font-semibold text-azul-600">Tipo de cliente</legend>
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-azul-50 p-1">
              {[
                { valor: 'persona', etiqueta: 'Persona' },
                { valor: 'establecimiento', etiqueta: 'Establecimiento' },
              ].map((opcion) => (
                <label key={opcion.valor} className="cursor-pointer">
                  <input
                    type="radio"
                    name="tipo-cliente"
                    value={opcion.valor}
                    checked={datos.tipo === opcion.valor}
                    onChange={() => {
                      setDatos((actuales) => ({ ...actuales, tipo: opcion.valor }))
                      setErrores({})
                    }}
                    className="peer sr-only"
                  />
                  <span className="flex h-9 items-center justify-center rounded-md text-xs font-semibold text-azul-600 peer-checked:bg-blanco peer-checked:text-azul-950 peer-checked:shadow-sm peer-focus-visible:outline-2 peer-focus-visible:outline-azul-600">
                    {opcion.etiqueta}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-3 sm:grid-cols-2">
            <CampoCliente
              id={`${id}-nombre`}
              etiqueta={esEstablecimiento ? 'Nombre del establecimiento' : 'Nombre completo'}
              name="nombre"
              autoComplete={esEstablecimiento ? 'organization' : 'name'}
              maxLength={120}
              required
              placeholder={esEstablecimiento ? 'Ej. Taller El Rayo' : 'Ej. Carlos Ramírez'}
              value={datos.nombre}
              onChange={(evento) => cambiar('nombre', evento.target.value)}
              error={errores.nombre}
            />
            <CampoCliente
              id={`${id}-telefono`}
              etiqueta="Teléfono"
              name="telefono"
              type="tel"
              autoComplete="tel"
              maxLength={20}
              required
              placeholder="Número de contacto"
              value={datos.telefono}
              onChange={(evento) => cambiar('telefono', evento.target.value)}
              error={errores.telefono}
            />
            {!esEstablecimiento && (
              <div className="flex min-w-0 flex-col gap-1.5">
                <label htmlFor={`${id}-tipo-documento`} className="text-xs font-semibold text-azul-600">
                  Tipo de documento
                </label>
                <select
                  id={`${id}-tipo-documento`}
                  value={datos.tipoDocumento}
                  onChange={(evento) => cambiar('tipoDocumento', evento.target.value)}
                  className="h-10 w-full rounded-lg border border-azul-200 bg-blanco px-3 text-sm text-azul-950 outline-none focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
                >
                  <option value="cedula">Cédula de ciudadanía</option>
                  <option value="cedula_extranjeria">Cédula de extranjería</option>
                  <option value="pasaporte">Pasaporte</option>
                  <option value="tarjeta_identidad">Tarjeta de identidad</option>
                </select>
              </div>
            )}
            <CampoCliente
              id={`${id}-documento`}
              etiqueta={esEstablecimiento ? 'NIT' : 'Número de documento'}
              name="documento"
              maxLength={30}
              required
              placeholder={esEstablecimiento ? 'NIT del establecimiento' : 'Número de documento'}
              value={datos.documento}
              onChange={(evento) => cambiar('documento', evento.target.value)}
              error={errores.documento}
            />
            {esEstablecimiento ? (
              <>
                <div className="flex min-w-0 flex-col gap-1.5">
                  <label htmlFor={`${id}-segmento`} className="text-xs font-semibold text-azul-600">
                    Tipo de establecimiento
                  </label>
                  <select
                    id={`${id}-segmento`}
                    value={datos.segmento}
                    onChange={(evento) => cambiar('segmento', evento.target.value)}
                    className="h-10 w-full rounded-lg border border-azul-200 bg-blanco px-3 text-sm text-azul-950 outline-none focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
                  >
                    <option value="bar">Bar</option>
                    <option value="restaurante">Restaurante</option>
                    <option value="tienda">Tienda</option>
                    <option value="distribuidor">Distribuidor</option>
                    <option value="otro">Otro</option>
                  </select>
                </div>
                <CampoCliente
                  id={`${id}-contacto`}
                  etiqueta="Persona de contacto"
                  name="contacto"
                  autoComplete="name"
                  maxLength={120}
                  placeholder="Opcional"
                  value={datos.contacto}
                  onChange={(evento) => cambiar('contacto', evento.target.value)}
                />
              </>
            ) : (
              <CampoCliente
                id={`${id}-fecha-nacimiento`}
                etiqueta="Fecha de nacimiento"
                name="fechaNacimiento"
                type="date"
                max={new Date().toISOString().slice(0, 10)}
                required
                value={datos.fechaNacimiento}
                onChange={(evento) => cambiar('fechaNacimiento', evento.target.value)}
                error={errores.fechaNacimiento}
              />
            )}
            <CampoCliente
              id={`${id}-correo`}
              etiqueta="Correo electrónico"
              name="correo"
              type="email"
              autoComplete="email"
              maxLength={150}
              placeholder="Opcional"
              value={datos.correo}
              onChange={(evento) => cambiar('correo', evento.target.value)}
              error={errores.correo}
            />
            <CampoCliente
              id={`${id}-ciudad`}
              etiqueta="Ciudad"
              name="ciudad"
              autoComplete="address-level2"
              maxLength={100}
              placeholder="Opcional"
              value={datos.ciudad}
              onChange={(evento) => cambiar('ciudad', evento.target.value)}
            />
          </div>

          {Object.values(errores).some(Boolean) && (
            <Aviso>Revisa los campos marcados antes de guardar.</Aviso>
          )}

          <footer className="flex justify-end gap-2">
            <button
              type="button"
              onClick={alCerrar}
              className="h-10 rounded-lg border border-azul-200 bg-blanco px-4 text-xs font-semibold text-azul-600 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-azul-950 px-4 text-xs font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
            >
              <CheckIcon size={16} weight="bold" /> Guardar cliente
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
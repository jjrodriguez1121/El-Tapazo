import { useId, useState } from 'react'
import { CheckIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import {
  validarCorreoOpcional,
  validarDocumento,
  validarObligatorio,
  validarTelefono,
} from '@/utilidades/validaciones'

function CampoProveedor({ etiqueta, id, error = '', className = '', ...props }) {
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

export default function ModalNuevoProveedor({ alCerrar, alCrear, proveedoresExistentes = [] }) {
  const id = useId()
  const [datos, setDatos] = useState({
    razonSocial: '',
    nit: '',
    nombreContacto: '',
    telefono: '',
    correo: '',
    ciudad: '',
    direccion: '',
  })
  const [errores, setErrores] = useState({})

  function cambiar(campo, valor) {
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))
    setErrores((actuales) => ({ ...actuales, [campo]: '' }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const razonSocial = datos.razonSocial.trim()
    const nit = datos.nit.trim()
    const nuevosErrores = {
      razonSocial: validarObligatorio(razonSocial, 'Escribe la razón social.'),
      nit: nit ? validarDocumento(nit, 'El NIT') : '',
      telefono: datos.telefono.trim() ? validarTelefono(datos.telefono) : '',
      correo: validarCorreoOpcional(datos.correo),
    }
    const razonSocialNormalizada = razonSocial.toLocaleLowerCase('es-CO')
    const nitNormalizado = nit.replace(/[^a-z\d]/gi, '').toUpperCase()

    if (!nuevosErrores.razonSocial && proveedoresExistentes.some(
      (proveedor) => (proveedor.razonSocial ?? proveedor.razon_social ?? '')
        .trim()
        .toLocaleLowerCase('es-CO') === razonSocialNormalizada
    )) {
      nuevosErrores.razonSocial = 'Ya existe un proveedor con esa razón social.'
    }
    if (!nuevosErrores.nit && nitNormalizado && proveedoresExistentes.some(
      (proveedor) => (proveedor.nit ?? '').replace(/[^a-z\d]/gi, '').toUpperCase() === nitNormalizado
    )) {
      nuevosErrores.nit = 'Ya existe un proveedor con ese NIT.'
    }

    setErrores(nuevosErrores)
    if (Object.values(nuevosErrores).some(Boolean)) {
      return
    }

    alCrear({
      id: `local-${Date.now()}`,
      ...datos,
      razonSocial,
      nit,
      nombreContacto: datos.nombreContacto.trim(),
      telefono: datos.telefono.trim(),
      correo: datos.correo.trim(),
      ciudad: datos.ciudad.trim(),
      direccion: datos.direccion.trim(),
      cantidadProductos: 0,
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
          <h2 id={`${id}-titulo`} className="text-lg font-bold text-azul-950">
            Nuevo proveedor
          </h2>
          <p className="mt-1 text-xs font-medium text-azul-600">
            Registra los datos comerciales y de contacto.
          </p>
        </header>

        <form onSubmit={enviar} noValidate className="flex flex-col gap-4">
          <section className="rounded-lg border border-azul-150 p-4">
            <h3 className="mb-4 text-sm font-semibold text-azul-900">Información del proveedor</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <CampoProveedor
                id={`${id}-razon-social`}
                etiqueta="Razón social"
                name="razonSocial"
                autoComplete="organization"
                maxLength={150}
                required
                value={datos.razonSocial}
                onChange={(evento) => cambiar('razonSocial', evento.target.value)}
                error={errores.razonSocial}
              />
              <CampoProveedor
                id={`${id}-nit`}
                etiqueta="NIT"
                name="nit"
                maxLength={20}
                placeholder="Opcional"
                value={datos.nit}
                onChange={(evento) => cambiar('nit', evento.target.value)}
                error={errores.nit}
              />
              <CampoProveedor
                id={`${id}-contacto`}
                etiqueta="Nombre de contacto"
                name="nombreContacto"
                autoComplete="name"
                maxLength={120}
                placeholder="Opcional"
                value={datos.nombreContacto}
                onChange={(evento) => cambiar('nombreContacto', evento.target.value)}
              />
              <CampoProveedor
                id={`${id}-telefono`}
                etiqueta="Teléfono"
                name="telefono"
                type="tel"
                autoComplete="tel"
                maxLength={20}
                placeholder="Opcional"
                value={datos.telefono}
                onChange={(evento) => cambiar('telefono', evento.target.value)}
                error={errores.telefono}
              />
              <CampoProveedor
                id={`${id}-correo`}
                etiqueta="Correo"
                name="correo"
                type="email"
                autoComplete="email"
                maxLength={150}
                placeholder="Opcional"
                value={datos.correo}
                onChange={(evento) => cambiar('correo', evento.target.value)}
                error={errores.correo}
              />
              <CampoProveedor
                id={`${id}-ciudad`}
                etiqueta="Ciudad"
                name="ciudad"
                autoComplete="address-level2"
                maxLength={100}
                placeholder="Opcional"
                value={datos.ciudad}
                onChange={(evento) => cambiar('ciudad', evento.target.value)}
              />
              <CampoProveedor
                id={`${id}-direccion`}
                etiqueta="Dirección"
                name="direccion"
                autoComplete="street-address"
                maxLength={255}
                placeholder="Opcional"
                className="sm:col-span-2"
                value={datos.direccion}
                onChange={(evento) => cambiar('direccion', evento.target.value)}
              />
            </div>
          </section>

          {Object.values(errores).some(Boolean) && (
            <Aviso>Corrige los campos marcados antes de guardar.</Aviso>
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
              <CheckIcon size={16} weight="bold" /> Guardar proveedor
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
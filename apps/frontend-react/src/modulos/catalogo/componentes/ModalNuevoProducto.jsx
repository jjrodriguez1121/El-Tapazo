import { useId, useState } from 'react'
import {
  CheckIcon,
  ImageIcon,
  InfoIcon,
  TagIcon,
  UploadSimpleIcon,
} from '@phosphor-icons/react'

import {
  validarNumeroNoNegativo,
  validarObligatorio,
  validarSku,
} from '@/utilidades/validaciones'

const UNIDADES = ['Unidad', 'Caja', 'Paquete', 'Botella', 'Lata', 'Litro', 'Kilogramo', 'Metro']
const TAMANO_MAXIMO_DE_IMAGEN = 5 * 1024 * 1024

function CampoFormulario({ etiqueta, id, error = '', className = '', ...props }) {
  return (
    <div className={`flex min-w-0 flex-col gap-1.5 ${className}`}>
      <label htmlFor={id} className="text-xs font-semibold text-azul-700">
        {etiqueta}
      </label>
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        className="h-9 w-full rounded-lg border border-azul-200 bg-azul-50/40 px-3 text-sm text-azul-950 outline-none placeholder:text-azul-300 focus:border-azul-500 focus:bg-blanco focus:ring-3 focus:ring-azul-500/12"
        {...props}
      />
      {error && <p id={`${id}-error`} className="text-[11px] font-semibold text-error-700">{error}</p>}
    </div>
  )
}

function EncabezadoSeccion({ Icono, children }) {
  return (
    <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-azul-900">
      <Icono size={17} weight="bold" className="text-exito-700" />
      {children}
    </h3>
  )
}

export default function ModalNuevoProducto({
  categorias,
  alCerrar,
  alCrear,
  productoParaEditar = null,
  existencias = [],
  productosExistentes = [],
}) {
  const id = useId()
  const estaEditando = Boolean(productoParaEditar)
  const [datos, setDatos] = useState({
    nombre: productoParaEditar?.nombre ?? '',
    sku: productoParaEditar?.sku ?? '',
    categoriaId: productoParaEditar?.categoria?.id
      ? String(productoParaEditar.categoria.id)
      : categorias[0]?.id
        ? String(categorias[0].id)
        : '',
    unidad: productoParaEditar?.unidad ?? 'Unidad',
    precioVenta: productoParaEditar?.precio_evento != null
      ? String(productoParaEditar.precio_evento)
      : '',
    stockActual: existencias.length
      ? String(existencias.reduce((total, existencia) => total + Number(existencia.cantidad_disponible), 0))
      : '',
    stockMinimo: existencias.length
      ? String(existencias.reduce((total, existencia) => total + Number(existencia.cantidad_minima ?? 0), 0))
      : '',
    ubicacion: existencias.map((existencia) => existencia.ubicacion.nombre).join(', '),
  })
  const [imagen, setImagen] = useState(
    productoParaEditar?.imagen
      ? { nombre: 'Imagen actual', vistaPrevia: productoParaEditar.imagen }
      : null
  )
  const [errores, setErrores] = useState({})
  const [arrastrando, setArrastrando] = useState(false)

  function cambiar(campo, valor) {
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))
    setErrores((actuales) => ({ ...actuales, [campo]: '' }))
  }

  function seleccionarImagen(archivo) {
    if (!archivo) return
    if (!['image/png', 'image/jpeg'].includes(archivo.type)) {
      setErrores((actuales) => ({ ...actuales, imagen: 'La imagen debe estar en formato PNG o JPG.' }))
      return
    }
    if (archivo.size > TAMANO_MAXIMO_DE_IMAGEN) {
      setErrores((actuales) => ({ ...actuales, imagen: 'La imagen no puede superar los 5 MB.' }))
      return
    }

    const lector = new FileReader()
    lector.onload = () => setImagen({ nombre: archivo.name, vistaPrevia: lector.result })
    lector.readAsDataURL(archivo)
    setErrores((actuales) => ({ ...actuales, imagen: '' }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const nuevosErrores = {
      nombre: validarObligatorio(datos.nombre, 'Escribe el nombre del producto.'),
      sku: validarSku(datos.sku),
      categoriaId: validarObligatorio(datos.categoriaId, 'Selecciona una categoría.'),
      precioVenta: validarNumeroNoNegativo(datos.precioVenta, 'El precio de venta'),
      stockActual: validarNumeroNoNegativo(datos.stockActual, 'El stock actual', { entero: true }),
      stockMinimo: validarNumeroNoNegativo(datos.stockMinimo, 'El stock mínimo', { entero: true }),
      ubicacion: validarObligatorio(datos.ubicacion, 'Escribe la ubicación del producto.'),
    }

    const categoria = categorias.find((opcion) => String(opcion.id) === datos.categoriaId)
    if (!nuevosErrores.categoriaId && !categoria) {
      nuevosErrores.categoriaId = 'Selecciona una categoría válida.'
    }

    const skuNormalizado = datos.sku.trim().toUpperCase()
    const skuDuplicado = productosExistentes.some(
      (producto) =>
        String(producto.id) !== String(productoParaEditar?.id) &&
        producto.sku.trim().toUpperCase() === skuNormalizado
    )
    if (!nuevosErrores.sku && skuDuplicado) {
      nuevosErrores.sku = 'Ya existe un producto con ese SKU.'
    }

    setErrores(nuevosErrores)
    if (Object.values(nuevosErrores).some(Boolean)) {
      return
    }

    alCrear({
      nombre: datos.nombre.trim(),
      sku: datos.sku.trim(),
      categoria,
      unidad: datos.unidad,
      precioVenta: Number(datos.precioVenta),
      stockActual: Number(datos.stockActual),
      stockMinimo: Number(datos.stockMinimo),
      ubicacion: datos.ubicacion.trim(),
      imagen: imagen?.vistaPrevia ?? '',
    })
    alCerrar()
  }

  function recibirArchivo(evento) {
    evento.preventDefault()
    setArrastrando(false)
    seleccionarImagen(evento.dataTransfer.files[0])
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-azul-950/45 px-3 py-5 sm:px-6 sm:py-8">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-titulo`}
        className="mx-auto w-full max-w-4xl"
      >
        <header className="mb-4 flex items-start justify-between gap-4 px-1">
          <div>
            <h2 id={`${id}-titulo`} className="text-xl font-bold text-azul-950">
              {estaEditando ? 'Editar producto' : 'Nuevo producto'}
            </h2>
            <p className="mt-1 text-xs font-medium text-azul-500">
              Completa la información del repuesto.
            </p>
          </div>
          <button
            type="button"
            aria-label="Cerrar formulario"
            onClick={alCerrar}
            className="grid size-9 place-items-center rounded-lg text-azul-500 hover:bg-blanco/70 focus-visible:outline-2 focus-visible:outline-azul-500"
          >
            <span aria-hidden="true" className="text-xl leading-none">×</span>
          </button>
        </header>

        <form onSubmit={enviar} noValidate className="flex flex-col gap-3">
          <section className="rounded-xl border border-azul-150 bg-blanco p-4 sm:p-5">
            <EncabezadoSeccion Icono={InfoIcon}>Información general</EncabezadoSeccion>
            <div className="grid gap-x-3 gap-y-3 sm:grid-cols-[2fr_1fr]">
              <CampoFormulario
                id={`${id}-nombre`}
                etiqueta="Nombre del repuesto"
                name="nombre"
                required
                autoComplete="off"
                maxLength={200}
                value={datos.nombre}
                onChange={(evento) => cambiar('nombre', evento.target.value)}
                error={errores.nombre}
              />
              <CampoFormulario
                id={`${id}-sku`}
                etiqueta="Código / SKU"
                name="sku"
                required
                autoComplete="off"
                maxLength={50}
                value={datos.sku}
                onChange={(evento) => cambiar('sku', evento.target.value)}
                error={errores.sku}
              />

              <div className="flex min-w-0 flex-col gap-1.5">
                <label htmlFor={`${id}-categoria`} className="text-xs font-semibold text-azul-700">
                  Categoría
                </label>
                <select
                  id={`${id}-categoria`}
                  name="categoria"
                  required
                  aria-invalid={Boolean(errores.categoriaId)}
                  aria-describedby={errores.categoriaId ? `${id}-categoria-error` : undefined}
                  value={datos.categoriaId}
                  onChange={(evento) => cambiar('categoriaId', evento.target.value)}
                  className="h-9 w-full rounded-lg border border-azul-200 bg-azul-50/40 px-3 text-sm text-azul-950 outline-none focus:border-azul-500 focus:bg-blanco focus:ring-3 focus:ring-azul-500/12"
                >
                  {categorias.map((categoria) => (
                    <option key={categoria.id} value={categoria.id}>{categoria.nombre}</option>
                  ))}
                </select>
                {errores.categoriaId && (
                  <p id={`${id}-categoria-error`} className="text-[11px] font-semibold text-error-700">
                    {errores.categoriaId}
                  </p>
                )}
              </div>

              <div className="flex min-w-0 flex-col gap-1.5">
                <label htmlFor={`${id}-unidad`} className="text-xs font-semibold text-azul-700">
                  Unidad de medida
                </label>
                <select
                  id={`${id}-unidad`}
                  name="unidad"
                  value={datos.unidad}
                  onChange={(evento) => cambiar('unidad', evento.target.value)}
                  className="h-9 w-full rounded-lg border border-azul-200 bg-azul-50/40 px-3 text-sm text-azul-950 outline-none focus:border-azul-500 focus:bg-blanco focus:ring-3 focus:ring-azul-500/12"
                >
                  {UNIDADES.map((unidad) => <option key={unidad}>{unidad}</option>)}
                </select>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-azul-150 bg-blanco p-4 sm:p-5">
            <EncabezadoSeccion Icono={TagIcon}>Precio e inventario</EncabezadoSeccion>
            <div className="grid gap-x-3 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
              <CampoFormulario
                id={`${id}-precio`}
                etiqueta="Precio de venta"
                name="precioVenta"
                type="number"
                required
                min="0"
                step="0.01"
                inputMode="decimal"
                value={datos.precioVenta}
                onChange={(evento) => cambiar('precioVenta', evento.target.value)}
                error={errores.precioVenta}
              />
              <CampoFormulario
                id={`${id}-stock`}
                etiqueta="Stock actual"
                name="stockActual"
                type="number"
                required
                min="0"
                step="1"
                value={datos.stockActual}
                onChange={(evento) => cambiar('stockActual', evento.target.value)}
                error={errores.stockActual}
              />
              <CampoFormulario
                id={`${id}-minimo`}
                etiqueta="Stock mínimo"
                name="stockMinimo"
                type="number"
                required
                min="0"
                step="1"
                value={datos.stockMinimo}
                onChange={(evento) => cambiar('stockMinimo', evento.target.value)}
                error={errores.stockMinimo}
              />
              <CampoFormulario
                id={`${id}-ubicacion`}
                etiqueta="Ubicación"
                name="ubicacion"
                maxLength={100}
                required
                placeholder="Ej. Bodega A-12"
                value={datos.ubicacion}
                onChange={(evento) => cambiar('ubicacion', evento.target.value)}
                error={errores.ubicacion}
              />
            </div>
          </section>

          <section className="rounded-xl border border-azul-150 bg-blanco p-4 sm:p-5">
            <EncabezadoSeccion Icono={ImageIcon}>Imagen del producto</EncabezadoSeccion>
            <label
              htmlFor={`${id}-imagen`}
              onDragOver={(evento) => {
                evento.preventDefault()
                setArrastrando(true)
              }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={recibirArchivo}
              className={`flex min-h-24 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed px-4 py-4 text-center transition-colors ${arrastrando ? 'border-azul-800 bg-azul-50' : 'border-azul-200 bg-azul-50/30 hover:bg-azul-50'}`}
            >
              <input
                id={`${id}-imagen`}
                type="file"
                accept="image/png,image/jpeg"
                className="sr-only"
                onChange={(evento) => seleccionarImagen(evento.target.files[0])}
              />
              {imagen ? (
                <>
                  <img src={imagen.vistaPrevia} alt="Vista previa del producto" className="mb-2 max-h-24 rounded-md object-contain" />
                  <span className="text-xs font-semibold text-azul-800">{imagen.nombre}</span>
                  <span className="text-[11px] text-azul-500">Haz clic para cambiar la imagen</span>
                </>
              ) : (
                <>
                  <UploadSimpleIcon size={21} className="text-azul-500" />
                  <span className="text-xs font-medium text-azul-700">Arrastra una imagen o haz clic para subir</span>
                  <span className="text-[10px] text-azul-400">PNG o JPG · máx. 5 MB</span>
                </>
              )}
            </label>
          </section>

          {errores.imagen && <p role="alert" className="text-xs font-semibold text-error-700">{errores.imagen}</p>}

          <footer className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={alCerrar}
              className="h-10 rounded-lg border border-azul-200 bg-blanco px-4 text-xs font-semibold text-azul-700 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-500"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-azul-950 px-4 text-xs font-bold text-blanco hover:bg-azul-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azul-600"
            >
              <CheckIcon size={16} weight="bold" />
              {estaEditando ? 'Guardar cambios' : 'Guardar producto'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
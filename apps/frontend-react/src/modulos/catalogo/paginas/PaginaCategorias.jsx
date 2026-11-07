import { useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'

import ModalNuevaCategoria from '../componentes/ModalNuevaCategoria'
import TarjetaDeCategoria from '../componentes/TarjetaDeCategoria'
import { CATEGORIAS_DE_EJEMPLO } from '../utilidades/datosDeEjemplo'

/**
 * Pantalla principal de Categorías del catálogo.
 * Muestra la cuadrícula de categorías con sus productos asociados y la opción
 * de crear una nueva categoría.
 */
export default function PaginaCategorias() {
  const [categorias, setCategorias] = useState(CATEGORIAS_DE_EJEMPLO)
  const [modalAbierto, setModalAbierto] = useState(false)

  function agregarCategoria(categoria) {
    setCategorias((actuales) => [...actuales, { ...categoria, cantidadProductos: 0 }])
  }

  return (
    <div className="space-y-6">
      {/* Encabezado con título, subtítulo y botón de acción */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold tracking-tight text-azul-950">
            Categorías
          </h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            Organización del catálogo de productos
          </p>
        </div>

        <div>
          <button
            type="button"
            onClick={() => setModalAbierto(true)}
            className="flex items-center gap-2 rounded-xl bg-exito-700 px-4.5 py-2.5 text-sm font-semibold text-blanco shadow-sm transition-colors hover:bg-exito-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-exito-600 active:scale-[0.98] cursor-pointer"
          >
            <PlusIcon size={18} weight="bold" />
            <span>Nueva categoría</span>
          </button>
        </div>
      </header>

      {/* Cuadrícula de tarjetas de categorías */}
      <section aria-label="Listado de categorías">
        <div className="grid grid-cols-1 gap-4.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
          {categorias.map((categoria) => (
            <TarjetaDeCategoria
              key={categoria.id}
              nombre={categoria.nombre}
              cantidadProductos={categoria.cantidadProductos}
              Icono={categoria.Icono}
            />
          ))}
        </div>
      </section>

      {modalAbierto && (
        <ModalNuevaCategoria
          alCerrar={() => setModalAbierto(false)}
          alCrear={agregarCategoria}
          categoriasExistentes={categorias}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

import ModalNuevaCategoria from '../componentes/ModalNuevaCategoria'
import TarjetaDeCategoria from '../componentes/TarjetaDeCategoria'
import EsqueletoDeCategorias from '../componentes/EsqueletoDeCategorias'
import Aviso from '@/componentes/ui/Aviso'
import { mensajeDeError } from '@/utilidades/errores'
import { desactivarCategoria } from '../api/apiCategorias'
import {
  CLAVE_CATALOGO_PRODUCTOS,
  useCatalogoDeProductos,
} from '../hooks/useCatalogoDeProductos'

/**
 * Pantalla principal de Categorías del catálogo.
 * Muestra la cuadrícula de categorías con sus productos asociados y la opción
 * de crear una nueva categoría.
 */
export default function PaginaCategorias() {
  const catalogo = useCatalogoDeProductos()
  const navegar = useNavigate()
  const clienteConsultas = useQueryClient()
  const [modalAbierto, setModalAbierto] = useState(false)
  const [categoriaParaEditar, setCategoriaParaEditar] = useState(null)

  function agregarCategoria(categoria) {
    clienteConsultas.setQueryData(CLAVE_CATALOGO_PRODUCTOS, (actual) => {
      if (!actual) return actual
      return {
        ...actual,
        categorias: [
          ...actual.categorias,
          { ...categoria, cantidadProductos: 0 },
        ],
      }
    })
    clienteConsultas.invalidateQueries({ queryKey: CLAVE_CATALOGO_PRODUCTOS })
  }

  function actualizarCategoria(categoriaActualizada) {
    clienteConsultas.setQueryData(CLAVE_CATALOGO_PRODUCTOS, (actual) => ({
      ...actual,
      categorias: actual.categorias.map((categoria) =>
        categoria.id === categoriaActualizada.id
          ? { ...categoria, ...categoriaActualizada }
          : categoria
      ),
    }))
  }

  async function eliminarCategoria(categoria) {
    if (!window.confirm(`¿Eliminar la categoría ${categoria.nombre}?`)) return
    await desactivarCategoria(categoria.id)
    clienteConsultas.setQueryData(CLAVE_CATALOGO_PRODUCTOS, (actual) => ({
      ...actual,
      categorias: actual.categorias.filter((item) => item.id !== categoria.id),
    }))
  }

  if (catalogo.isPending) return <EsqueletoDeCategorias />

  if (catalogo.isError) {
    return (
      <section className="flex flex-col gap-4">
        <h1 className="text-titulo font-bold text-azul-950">Categorías</h1>
        <Aviso>{mensajeDeError(catalogo.error)}</Aviso>
      </section>
    )
  }

  const categorias = catalogo.data.categorias

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
            onClick={() => { setCategoriaParaEditar(null); setModalAbierto(true) }}
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
              onClick={() => navegar(`/productos?categoria=${categoria.id}`)}
              alEditar={() => { setCategoriaParaEditar(categoria); setModalAbierto(true) }}
              alEliminar={() => eliminarCategoria(categoria)}
            />
          ))}
        </div>
      </section>

      {modalAbierto && (
        <ModalNuevaCategoria
          alCerrar={() => setModalAbierto(false)}
          alCrear={agregarCategoria}
          alActualizar={actualizarCategoria}
          categoriasExistentes={categorias}
          categoriaParaEditar={categoriaParaEditar}
        />
      )}
    </div>
  )
}

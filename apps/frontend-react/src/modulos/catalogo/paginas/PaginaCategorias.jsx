import { useState } from 'react'
import { PlusIcon } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

import ModalNuevaCategoria from '../componentes/ModalNuevaCategoria'
import TarjetaDeCategoria from '../componentes/TarjetaDeCategoria'
import EsqueletoDeCategorias from '../componentes/EsqueletoDeCategorias'
import { activarCategoria, desactivarCategoria } from '../api/apiCategorias'
import {
  CLAVE_CATALOGO_PRODUCTOS,
  CLAVE_TODAS_LAS_CATEGORIAS,
  useCatalogoDeProductos,
  useTodasLasCategorias,
} from '../hooks/useCatalogoDeProductos'
import Aviso from '@/componentes/ui/Aviso'
import ConfirmacionAccion from '@/componentes/ui/ConfirmacionAccion'
import useFiltroPersistente from '@/hooks/useFiltroPersistente'
import { mensajeDeError } from '@/utilidades/errores'

/**
 * Pantalla principal de Categorías del catálogo.
 * Muestra la cuadrícula de categorías con sus productos asociados y la opción
 * de crear una nueva categoría.
 */
export default function PaginaCategorias() {
  const catalogo = useCatalogoDeProductos()
  const consultaCategorias = useTodasLasCategorias()
  const navegar = useNavigate()
  const clienteConsultas = useQueryClient()
  const [modalAbierto, setModalAbierto] = useState(false)
  const [categoriaParaEditar, setCategoriaParaEditar] = useState(null)
  const [filtroEstado, setFiltroEstado] = useFiltroPersistente('categorias.estado', 'activas')
  const [errorAccion, setErrorAccion] = useState('')
  const [categoriaParaCambiar, setCategoriaParaCambiar] = useState(null)
  const [procesandoEstado, setProcesandoEstado] = useState(false)

  function agregarCategoria(categoria) {
    clienteConsultas.setQueryData(CLAVE_TODAS_LAS_CATEGORIAS, (actual = []) => [
      categoria,
      ...actual,
    ])
    clienteConsultas.invalidateQueries({ queryKey: CLAVE_CATALOGO_PRODUCTOS })
  }

  function actualizarCategoria(categoriaActualizada) {
    clienteConsultas.setQueryData(CLAVE_TODAS_LAS_CATEGORIAS, (actual = []) =>
      actual.map((categoria) =>
        categoria.id === categoriaActualizada.id
          ? { ...categoria, ...categoriaActualizada }
          : categoria
      )
    )
    clienteConsultas.invalidateQueries({ queryKey: CLAVE_CATALOGO_PRODUCTOS })
  }

  async function cambiarEstadoCategoria() {
    const categoria = categoriaParaCambiar
    if (!categoria) return
    const activar = !categoria.activa
    setProcesandoEstado(true)
    setErrorAccion('')
    try {
      const actualizada = activar
        ? await activarCategoria(categoria.id)
        : await desactivarCategoria(categoria.id)
      clienteConsultas.setQueryData(CLAVE_TODAS_LAS_CATEGORIAS, (actual = []) =>
        actual.map((item) => (item.id === actualizada.id ? { ...item, ...actualizada } : item))
      )
      await clienteConsultas.invalidateQueries({ queryKey: CLAVE_CATALOGO_PRODUCTOS })
      setCategoriaParaCambiar(null)
    } catch (error) {
      setErrorAccion(mensajeDeError(error))
      setCategoriaParaCambiar(null)
    } finally {
      setProcesandoEstado(false)
    }
  }

  if (catalogo.isPending || consultaCategorias.isPending) return <EsqueletoDeCategorias />

  if (catalogo.isError || consultaCategorias.isError) {
    const error = catalogo.error ?? consultaCategorias.error
    return (
      <section className="flex flex-col gap-4">
        <h1 className="text-titulo font-bold text-azul-950">Categorías</h1>
        <Aviso>{mensajeDeError(error)}</Aviso>
      </section>
    )
  }

  const categorias = consultaCategorias.data.map((categoria) => ({
    ...categoria,
    activa: categoria.activa ?? true,
    cantidadProductos: catalogo.data.productos.filter(
      (producto) => String(producto.categoria?.id) === String(categoria.id)
    ).length,
  }))
  const categoriasFiltradas = categorias.filter(
    (categoria) => filtroEstado === 'todas' || categoria.activa === (filtroEstado === 'activas')
  )

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-titulo font-bold tracking-tight text-azul-950">Categorías</h1>
          <p className="mt-1 text-sm font-medium text-azul-400">
            Organización del catálogo de productos
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setCategoriaParaEditar(null)
            setModalAbierto(true)
          }}
          className="flex cursor-pointer items-center gap-2 rounded-xl bg-exito-700 px-4.5 py-2.5 text-sm font-semibold text-blanco shadow-sm transition-colors hover:bg-exito-800 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-exito-600 active:scale-[0.98]"
        >
          <PlusIcon size={18} weight="bold" />
          <span>Nueva categoría</span>
        </button>
      </header>

      {errorAccion && <Aviso>{errorAccion}</Aviso>}

      <label className="flex items-center gap-2 self-start text-xs font-semibold text-azul-600">
        Estado
        <select
          aria-label="Estado de las categorías"
          value={filtroEstado}
          onChange={(evento) => setFiltroEstado(evento.target.value)}
          className="h-9 rounded-lg border border-azul-150 bg-blanco px-3 text-xs text-azul-800 outline-none focus:border-azul-600 focus:ring-3 focus:ring-azul-600/15"
        >
          <option value="activas">Activas</option>
          <option value="inactivas">Inactivas</option>
          <option value="todas">Todas</option>
        </select>
      </label>

      <section aria-label="Listado de categorías">
        <div className="grid grid-cols-1 gap-4.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
          {categoriasFiltradas.map((categoria) => (
            <TarjetaDeCategoria
              key={categoria.id}
              nombre={categoria.nombre}
              cantidadProductos={categoria.cantidadProductos}
              activa={categoria.activa}
              Icono={categoria.Icono}
              onClick={() => navegar(`/productos?categoria=${categoria.id}`)}
              alEditar={() => {
                setCategoriaParaEditar(categoria)
                setModalAbierto(true)
              }}
              alCambiarEstado={() => setCategoriaParaCambiar(categoria)}
            />
          ))}
          {!categoriasFiltradas.length && (
            <p className="col-span-full rounded-xl border border-dashed border-azul-200 bg-blanco px-4 py-10 text-center text-sm text-azul-500">
              No hay categorías en este estado.
            </p>
          )}
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
      {categoriaParaCambiar && (
        <ConfirmacionAccion
          titulo={`${categoriaParaCambiar.activa ? 'Desactivar' : 'Activar'} categoría`}
          descripcion={
            categoriaParaCambiar.activa
              ? `¿Deseas desactivar «${categoriaParaCambiar.nombre}»? No se eliminarán sus productos y podrás volver a activarla después.`
              : `¿Deseas activar «${categoriaParaCambiar.nombre}» para volver a usarla en el catálogo?`
          }
          textoConfirmar={
            categoriaParaCambiar.activa ? 'Desactivar categoría' : 'Activar categoría'
          }
          variante={categoriaParaCambiar.activa ? 'destructiva' : 'positiva'}
          procesando={procesandoEstado}
          alConfirmar={cambiarEstadoCategoria}
          alCancelar={() => setCategoriaParaCambiar(null)}
        />
      )}
    </div>
  )
}

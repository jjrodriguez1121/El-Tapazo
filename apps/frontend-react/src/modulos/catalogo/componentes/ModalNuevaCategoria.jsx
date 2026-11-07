import { useId, useState } from 'react'
import { XIcon } from '@phosphor-icons/react'

import Aviso from '@/componentes/ui/Aviso'
import Boton from '@/componentes/ui/Boton'
import CampoTexto from '@/componentes/ui/CampoTexto'
import { mensajeDeError } from '@/utilidades/errores'
import { validarObligatorio } from '@/utilidades/validaciones'

import { useCrearCategoria } from '../hooks/useCrearCategoria'

const LARGO_MAXIMO_DEL_NOMBRE = 100
const LARGO_MAXIMO_DE_LA_DESCRIPCION = 255

export default function ModalNuevaCategoria({ alCerrar, alCrear, categoriasExistentes = [] }) {
	const [nombre, setNombre] = useState('')
	const [descripcion, setDescripcion] = useState('')
	const [errorDelNombre, setErrorDelNombre] = useState('')
	const idDescripcion = useId()
	const creacion = useCrearCategoria()

	function enviar(evento) {
		evento.preventDefault()
		const nombreLimpio = nombre.trim()
		let error = validarObligatorio(nombreLimpio, 'Escribe el nombre de la categoría.')

		if (!error && categoriasExistentes.some(
			(categoria) => categoria.nombre.trim().toLocaleLowerCase('es-CO') === nombreLimpio.toLocaleLowerCase('es-CO')
		)) {
			error = 'Ya existe una categoría con ese nombre.'
		}

		if (error) {
			setErrorDelNombre(error)
			return
		}

		setErrorDelNombre('')
		creacion.mutate(
			{ nombre: nombreLimpio, descripcion: descripcion.trim() },
			{
				onSuccess: (categoria) => {
					alCrear(categoria)
					alCerrar()
				},
			}
		)
	}

	return (
		<div className="fixed inset-0 z-50 grid place-items-center bg-azul-950/45 p-4">
			<section
				role="dialog"
				aria-modal="true"
				aria-labelledby="titulo-modal-categoria"
				className="w-full max-w-lg rounded-2xl bg-blanco p-6 shadow-xl"
			>
				<header className="mb-6 flex items-start justify-between gap-4">
					<div>
						<h2 id="titulo-modal-categoria" className="text-lg font-bold text-azul-950">
							Nueva categoría
						</h2>
						<p className="mt-1 text-sm font-medium text-azul-400">
							Agrega una categoría al catálogo.
						</p>
					</div>
					<button
						type="button"
						aria-label="Cerrar"
						title="Cerrar"
						onClick={alCerrar}
						disabled={creacion.isPending}
						className="grid size-9 flex-none place-items-center rounded-lg text-azul-500 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-400 disabled:opacity-50"
					>
						<XIcon size={20} />
					</button>
				</header>

				<form onSubmit={enviar} noValidate className="flex flex-col gap-5">
					<CampoTexto
						etiqueta="Nombre"
						name="nombre"
						autoComplete="off"
						autoFocus
						maxLength={LARGO_MAXIMO_DEL_NOMBRE}
						placeholder="Ej. Cervezas"
						value={nombre}
						onChange={(evento) => {
							setNombre(evento.target.value)
							setErrorDelNombre('')
						}}
						error={errorDelNombre}
					/>

					<div className="flex flex-col gap-1.75">
						<label
							htmlFor={idDescripcion}
							className="flex items-center gap-2 text-etiqueta font-bold text-azul-600"
						>
							Descripción
							<span className="text-xs font-semibold text-azul-400">Opcional</span>
						</label>
						<textarea
							id={idDescripcion}
							name="descripcion"
							maxLength={LARGO_MAXIMO_DE_LA_DESCRIPCION}
							rows={3}
							placeholder="Describe esta categoría"
							value={descripcion}
							onChange={(evento) => setDescripcion(evento.target.value)}
							className="w-full resize-y rounded-xl border border-azul-200 bg-blanco px-3.5 py-3 text-base text-azul-950 outline-none placeholder:text-azul-300 focus:border-azul-600 focus:ring-3 focus:ring-azul-600/16"
						/>
					</div>

					{creacion.error && <Aviso>{mensajeDeError(creacion.error)}</Aviso>}

					<footer className="flex justify-end gap-3 pt-1">
						<button
							type="button"
							onClick={alCerrar}
							disabled={creacion.isPending}
							className="rounded-xl border border-azul-200 px-4 py-2.5 text-sm font-semibold text-azul-700 hover:bg-azul-50 focus-visible:outline-2 focus-visible:outline-azul-400 disabled:opacity-50"
						>
							Cancelar
						</button>
						<Boton type="submit" cargando={creacion.isPending}>
							Crear categoría
						</Boton>
					</footer>
				</form>
			</section>
		</div>
	)
}

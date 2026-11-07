import { useState } from 'react'

import CampoTexto from './CampoTexto'
import { EyeIcon, EyeSlashIcon } from '@phosphor-icons/react'

/** Un campo de contraseña con el botón para verla: en un bar se teclea a oscuras y con prisa. */
export default function CampoContrasena(props) {
  const [visible, setVisible] = useState(false)

  return (
    <CampoTexto
      {...props}
      type={visible ? 'text' : 'password'}
      accesorio={
        <button
          type="button"
          onClick={() => setVisible(!visible)}
          aria-label={visible ? 'Ocultar la contraseña' : 'Mostrar la contraseña'}
          className="absolute top-1.5 right-1.5 h-10 rounded-[10px] bg-azul-75 px-3 text-etiqueta font-bold text-azul-600 hover:bg-azul-100 focus-visible:outline-2 focus-visible:outline-azul-300"
        >
          {visible ? (
            <EyeSlashIcon size={20} aria-hidden="true" />
          ) : (
            <EyeIcon size={20} aria-hidden="true" />
          )}
        </button>
      }
    />
  )
}

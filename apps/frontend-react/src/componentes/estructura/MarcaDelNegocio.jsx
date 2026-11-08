import logoTapazo from '@/recursos/imagenes/logo-tapazo.png'

/** Marca de la distribuidora en la cabecera del menú principal. */
export default function MarcaDelNegocio() {
  return (
    <div className="flex justify-center px-2 pt-1 pb-7">
      <img
        src={logoTapazo}
        alt="Logo de El Tapazo"
        className="w-full max-w-44 rounded-2xl bg-blanco object-contain p-1.5 shadow-lg ring-1 ring-blanco/20"
      />
    </div>
  )
}

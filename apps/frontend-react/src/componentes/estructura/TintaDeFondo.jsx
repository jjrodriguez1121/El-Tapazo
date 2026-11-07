/**
 * Las tres manchas de tinta que se extienden detrás de las pantallas de acceso.
 * Pura decoración: el lector de pantalla no se entera y no roba ningún clic.
 */
export default function TintaDeFondo() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      <span className="absolute -bottom-35 -left-30 block size-105 animate-tinta-grande rounded-full blur-[6px] mancha-de-tinta-grande" />
      <span className="absolute -top-22.5 -right-22.5 block size-75 animate-tinta-mediana rounded-full blur-xs mancha-de-tinta-mediana" />
      <span className="absolute bottom-[12%] left-[38%] block size-45 animate-tinta-chica rounded-full blur-[3px] mancha-de-tinta-chica" />
    </div>
  )
}

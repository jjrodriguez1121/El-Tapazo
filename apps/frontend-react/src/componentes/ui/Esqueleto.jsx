/** Un bloque que brilla mientras llega el contenido de verdad. El tamaño lo pone quien lo usa. */
export default function Esqueleto({ className = '', retraso = '0ms' }) {
  return (
    <span
      aria-hidden="true"
      className={`block animate-brillo rounded-md brillo-de-esqueleto ${className}`}
      style={{ animationDelay: retraso }}
    />
  )
}

/** Una tarjeta blanca del tablero, con su título y, a la derecha, un dato o una insignia. */
export default function PanelDelTablero({ titulo, accesorio, children }) {
  return (
    <section className="rounded-tarjeta border border-azul-100 bg-blanco p-5.5">
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold">{titulo}</h2>
        {accesorio}
      </div>
      {children}
    </section>
  )
}

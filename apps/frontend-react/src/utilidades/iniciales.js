/** Las iniciales de las dos primeras palabras: «Ana Ríos» da «AR»; «Kevin» da «K». */
export function iniciales(nombre) {
  return nombre
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((palabra) => palabra[0])
    .join('')
    .toUpperCase()
}

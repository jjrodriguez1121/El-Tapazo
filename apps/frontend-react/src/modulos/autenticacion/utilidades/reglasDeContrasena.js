/*
 * Lo que tiene que cumplir una contraseña, en el orden en que se enseña.
 *
 * Es el espejo de `AUTH_PASSWORD_VALIDATORS` del backend: el formulario avisa
 * antes de enviar, pero quien decide es el backend. Si cambia una regla allá,
 * cambia aquí.
 */

export const LARGO_MINIMO_DE_CONTRASENA = 6
export const LARGO_MAXIMO_DE_CONTRASENA = 128

const REGLAS = [
  {
    id: 'largo',
    etiqueta: `Mínimo ${LARGO_MINIMO_DE_CONTRASENA} caracteres`,
    seCumple: (contrasena) => contrasena.length >= LARGO_MINIMO_DE_CONTRASENA,
  },
  {
    id: 'letra',
    etiqueta: 'Al menos una letra',
    seCumple: (contrasena) => /\p{L}/u.test(contrasena),
  },
  {
    id: 'numero',
    etiqueta: 'Al menos un número',
    seCumple: (contrasena) => /\p{Nd}/u.test(contrasena),
  },
]

/** Cada regla con su etiqueta y si ya se cumple. */
export const evaluarContrasena = (contrasena) =>
  REGLAS.map(({ id, etiqueta, seCumple }) => ({ id, etiqueta, cumplida: seCumple(contrasena) }))

export const contrasenaEsValida = (contrasena) =>
  REGLAS.every(({ seCumple }) => seCumple(contrasena))

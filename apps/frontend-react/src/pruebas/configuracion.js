import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'

afterEach(() => {
  const claves = Array.from({ length: sessionStorage.length }, (_, indice) =>
    sessionStorage.key(indice)
  )
  for (const clave of claves) {
    if (clave?.startsWith('el-tapazo:filtros:')) sessionStorage.removeItem(clave)
  }
})

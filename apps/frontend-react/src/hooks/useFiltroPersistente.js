import { useEffect, useState } from 'react'

const PREFIJO = 'el-tapazo:filtros:'

export default function useFiltroPersistente(clave, valorInicial, priorizarInicial = false) {
  const claveCompleta = `${PREFIJO}${clave}`
  const [valor, setValor] = useState(() => {
    if (priorizarInicial) return valorInicial
    const guardado = sessionStorage.getItem(claveCompleta)
    return guardado === null ? valorInicial : JSON.parse(guardado)
  })

  useEffect(() => {
    sessionStorage.setItem(claveCompleta, JSON.stringify(valor))
  }, [claveCompleta, valor])

  return [valor, setValor]
}

"""Reglas de negocio del inventario (escrituras).

Todo movimiento pasa por `movimientos.aplicar_movimientos`: es el único sitio
donde se escriben a la vez el kardex y el saldo cacheado.
"""

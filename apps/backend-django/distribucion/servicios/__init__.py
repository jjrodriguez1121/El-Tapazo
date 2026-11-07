"""Reglas de negocio del canal mayorista (escrituras).

El stock sale **al despachar** y vuelve **al no poder entregar** (decisiones 4
y 5). Las dos cosas pasan por `inventario/servicios/consumo.py`, la misma
puerta que usa la barra: el signo, el tipo y la forma de devolver lo que se
movió se deciden una vez y no una vez por canal.
"""

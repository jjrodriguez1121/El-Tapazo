"""Consultas de negocio del catálogo (solo lectura)."""

from catalogo.selectores.productos import (
    buscar_por_sku,
    categorias_del_negocio,
    comparar_precios_de_proveedores,
    margen_de_venta,
    obtener_categoria,
    obtener_producto,
    obtener_proveedor,
    productos_del_negocio,
    proveedores_del_negocio,
)

__all__ = [
    "buscar_por_sku",
    "categorias_del_negocio",
    "comparar_precios_de_proveedores",
    "margen_de_venta",
    "obtener_categoria",
    "obtener_producto",
    "obtener_proveedor",
    "productos_del_negocio",
    "proveedores_del_negocio",
]

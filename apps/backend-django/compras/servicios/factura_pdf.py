"""Buscador de coincidencias entre una factura de proveedor en PDF y el catálogo.

No usa IA. `lector_factura_pdf` saca el encabezado y los renglones del texto
del PDF, y `coincidencias_factura` cruza cada renglón con los productos del
negocio. Aquí solo se juntan las dos cosas con la base de datos.
"""

import re

from catalogo.models import Producto, Proveedor
from compras.servicios.coincidencias_factura import (
    EntradaDelCatalogo,
    compactar_codigo,
    cruzar_renglon,
)
from compras.servicios.lector_factura_pdf import (
    FacturaIlegible,
    extraer_renglones,
    leer_factura,
    normalizar_factura,
)
from inventario.models import Existencia

__all__ = ["FacturaIlegible", "analizar_factura"]


def _solo_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def _buscar_proveedor(negocio_id: int, nit: str, nombre: str, renglones: list[str]):
    proveedores = list(Proveedor.objects.filter(negocio_id=negocio_id, activo=True))
    impreso = _solo_digitos(nit)
    if impreso:
        for proveedor in proveedores:
            propio = _solo_digitos(proveedor.nit or proveedor.numero_documento)
            # Uno puede traer el dígito de verificación y el otro no.
            if len(propio) >= 6 and (impreso.startswith(propio) or propio.startswith(impreso)):
                return proveedor
    encabezado = normalizar_factura(" ".join(renglones[:12]))
    for proveedor in proveedores:
        razon = re.sub(
            r"\b(S\.?A\.?S\.?|LTDA\.?|S\.?A\.?)(?=\s|$)",
            "",
            normalizar_factura(proveedor.razon_social),
        ).strip()
        if len(razon) >= 5 and razon in encabezado:
            return proveedor
    return None


def _producto_como_dict(producto: Producto, stock: dict, puntaje: int) -> dict:
    return {
        "id": producto.id,
        "sku": producto.sku,
        "nombre": producto.nombre,
        "costo": str(producto.costo),
        "precio_venta": str(producto.precio_venta),
        "stock": str(stock.get(producto.id, 0)),
        "impuesto": (
            {"nombre": producto.impuesto.nombre, "porcentaje": str(producto.impuesto.porcentaje)}
            if producto.impuesto
            else None
        ),
        "similitud": puntaje / 100,
    }


def analizar_factura(negocio_id: int, contenido: bytes) -> dict:
    renglones = extraer_renglones(contenido)
    factura = leer_factura(renglones)

    productos = {
        p.id: p
        for p in Producto.objects.filter(negocio_id=negocio_id, activo=True).select_related(
            "impuesto"
        )
    }
    stock = dict(
        Existencia.objects.filter(negocio_id=negocio_id).values_list(
            "producto_id", "cantidad_disponible"
        )
    )
    catalogo = {
        p.id: EntradaDelCatalogo(p.id, p.nombre, tuple(c for c in (p.sku, p.codigo) if c))
        for p in productos.values()
    }
    por_codigo: dict[str, set[int]] = {}
    for entrada in catalogo.values():
        for codigo in entrada.codigos:
            compacto = compactar_codigo(codigo)
            if len(compacto) >= 3:
                por_codigo.setdefault(compacto, set()).add(entrada.producto_id)

    lineas = []
    for indice, linea in enumerate(factura.lineas):
        resultado = cruzar_renglon(linea.descripcion, linea.codigo, catalogo, por_codigo)
        cantidad = max(1, int(linea.cantidad.to_integral_value()))
        lineas.append(
            {
                "indice": indice,
                "codigo": linea.codigo,
                "descripcion": linea.descripcion[:200],
                "cantidad": cantidad,
                "costo_unitario": str(linea.costo_unitario),
                "total_impreso": str(linea.total_impreso) if linea.total_impreso else None,
                "estado": resultado.estado,
                "candidatos": [
                    _producto_como_dict(productos[producto_id], stock, puntaje)
                    for producto_id, puntaje in resultado.candidatos
                ],
            }
        )

    proveedor = _buscar_proveedor(negocio_id, factura.nit, factura.nombre_proveedor, renglones)
    return {
        "numero_factura": factura.numero_factura,
        "proveedor_detectado": {"nombre": factura.nombre_proveedor, "nit": factura.nit},
        "proveedor": (
            {"id": proveedor.id, "razon_social": proveedor.razon_social} if proveedor else None
        ),
        "lineas": lineas,
    }

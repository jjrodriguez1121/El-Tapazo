"""Lo que el asistente sabe del catálogo de un negocio.

Se arma una tabla compacta (SKU, nombre, categoría, precio y stock) que va en el
mensaje de sistema. Si el catálogo es grande, se priorizan los productos que
coinciden con lo que el usuario acaba de preguntar.
"""

from decimal import Decimal

from asistente.servicios.texto import normalizar, palabras
from catalogo.models import Producto
from inventario.models import Existencia

LIMITE_DE_PRODUCTOS = 400


def _formatear_pesos(valor: Decimal) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def productos_del_negocio(negocio_id: int):
    return (
        Producto.objects.filter(negocio_id=negocio_id, activo=True)
        .select_related("categoria", "impuesto")
        .order_by("nombre")
    )


def existencias_por_producto(negocio_id: int, producto_ids) -> dict[int, Decimal]:
    return dict(
        Existencia.objects.filter(negocio_id=negocio_id, producto_id__in=producto_ids).values_list(
            "producto_id", "cantidad_disponible"
        )
    )


def _priorizar(productos: list, consulta: str) -> list:
    """Deja primero los productos que mencionan alguna palabra de la consulta."""
    terminos = {p for p in palabras(consulta) if len(p) >= 3}
    if not terminos:
        return productos

    def relevancia(producto):
        texto = normalizar(f"{producto.nombre} {producto.sku} {producto.categoria.nombre}")
        return -sum(1 for termino in terminos if termino in texto)

    return sorted(productos, key=relevancia)


def contexto_del_catalogo(negocio_id: int, consulta: str = "") -> str:
    productos = list(productos_del_negocio(negocio_id))
    total = len(productos)
    if total > LIMITE_DE_PRODUCTOS:
        productos = _priorizar(productos, consulta)[:LIMITE_DE_PRODUCTOS]

    stock = existencias_por_producto(negocio_id, [p.id for p in productos])
    filas = []
    for producto in productos:
        cantidad = stock.get(producto.id)
        if not producto.controla_inventario:
            texto_stock = "no controla inventario"
        elif cantidad is None:
            texto_stock = "0"
        else:
            texto_stock = f"{cantidad.normalize():f}"
        filas.append(
            " | ".join(
                [
                    producto.sku,
                    producto.nombre,
                    producto.categoria.nombre,
                    _formatear_pesos(producto.precio_venta),
                    texto_stock,
                    str(producto.stock_minimo),
                ]
            )
        )

    encabezado = "SKU | Nombre | Categoría | Precio de venta | Stock disponible | Stock mínimo"
    nota = ""
    if total > len(productos):
        nota = (
            f"\n(El catálogo tiene {total} productos activos; aquí van los {len(productos)} "
            "más relacionados con la pregunta.)"
        )
    if not filas:
        return "El negocio todavía no tiene productos activos registrados."
    return f"{encabezado}\n" + "\n".join(filas) + nota

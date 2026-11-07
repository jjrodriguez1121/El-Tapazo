"""Errores propios del catálogo.

Los "no encontrado" no están aquí: para eso está `NoEncontradoEnEsteNegocio`
de `nucleo`, que responde igual tanto si la fila no existe como si es de otro
negocio. Distinguirlas ya sería contar de más.
"""

from nucleo.excepciones import ErrorDeNegocio


class FormatoSkuInvalido(ErrorDeNegocio):
    """El SKU no tiene la forma acordada (tres letras, guion y de 3 a 6 cifras)."""

    mensaje = "El SKU debe tener la forma ABC-123: tres letras, un guion y de 3 a 6 números."
    codigo = "formato_sku_invalido"
    status_http = 400


class SkuDuplicado(ErrorDeNegocio):
    """Ya hay un producto con ese SKU en el negocio."""

    mensaje = "Ya existe un producto con ese SKU en este negocio."
    codigo = "sku_duplicado"
    status_http = 409


class CategoriaDuplicada(ErrorDeNegocio):
    mensaje = "Ya existe una categoría con ese nombre en este negocio."
    codigo = "categoria_duplicada"
    status_http = 409


class NitDeProveedorDuplicado(ErrorDeNegocio):
    mensaje = "Ya hay un proveedor con ese NIT en este negocio."
    codigo = "nit_de_proveedor_duplicado"
    status_http = 409


class ProveedorYaAsociado(ErrorDeNegocio):
    """Ese proveedor ya tiene precio registrado para ese producto."""

    mensaje = "Ese proveedor ya está registrado para este producto."
    codigo = "proveedor_ya_asociado"
    status_http = 409

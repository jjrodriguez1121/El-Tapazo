"""Filtros de los listados del catálogo.

Se declaran aquí y no leyendo `request.query_params` a mano: así el filtro es
uno solo, sale documentado en `/api/docs/` y no hay forma de olvidarse de
escapar algo.
"""

from django.db.models import Q
from django_filters import rest_framework as filtros

from catalogo.models import Categoria, Producto, Proveedor


class ProductoFiltro(filtros.FilterSet):
    """`?categoria=3&activo=true&busqueda=aguila&proveedor_id=4`."""

    busqueda = filtros.CharFilter(method="filtrar_por_texto", label="Nombre o SKU")
    proveedor_id = filtros.NumberFilter(
        method="filtrar_por_proveedor", label="Proveedor con compras recibidas"
    )

    class Meta:
        model = Producto
        fields = ("categoria", "activo")

    def filtrar_por_texto(self, consulta, nombre_del_campo, valor):
        """Busca en el nombre y en el SKU a la vez, que es lo que hace quien busca."""
        return consulta.filter(Q(nombre__icontains=valor) | Q(sku__icontains=valor))

    def filtrar_por_proveedor(self, consulta, nombre_del_campo, valor):
        """Limita a productos comprados a ese proveedor en compras recibidas."""
        return consulta.filter(
            detalles_compra__compra__proveedor_id=valor,
            detalles_compra__compra__estado="RECIBIDA",
        ).distinct()


class CategoriaFiltro(filtros.FilterSet):
    class Meta:
        model = Categoria
        fields = ("activa",)


class ProveedorFiltro(filtros.FilterSet):
    busqueda = filtros.CharFilter(field_name="razon_social", lookup_expr="icontains")

    class Meta:
        model = Proveedor
        fields = ("activo", "ciudad")

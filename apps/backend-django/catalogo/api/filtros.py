"""Filtros de los listados del catálogo.

Se declaran aquí y no leyendo `request.query_params` a mano: así el filtro es
uno solo, sale documentado en `/api/docs/` y no hay forma de olvidarse de
escapar algo.
"""

from django.db.models import Q
from django_filters import rest_framework as filtros

from catalogo.models import Categoria, Producto, Proveedor


class ProductoFiltro(filtros.FilterSet):
    """`?categoria=3&activo=true&busqueda=aguila`."""

    busqueda = filtros.CharFilter(method="filtrar_por_texto", label="Nombre o SKU")

    class Meta:
        model = Producto
        fields = ("categoria", "activo")

    def filtrar_por_texto(self, consulta, nombre_del_campo, valor):
        """Busca en el nombre y en el SKU a la vez, que es lo que hace quien busca."""
        return consulta.filter(Q(nombre__icontains=valor) | Q(sku__icontains=valor))


class CategoriaFiltro(filtros.FilterSet):
    class Meta:
        model = Categoria
        fields = ("activa",)


class ProveedorFiltro(filtros.FilterSet):
    busqueda = filtros.CharFilter(field_name="razon_social", lookup_expr="icontains")

    class Meta:
        model = Proveedor
        fields = ("activo", "ciudad")

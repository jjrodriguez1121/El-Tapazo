"""Filtros del listado de clientes."""

from django.db.models import Q
from django_filters import rest_framework as filtros

from clientes.models import Cliente


class ClienteFiltro(filtros.FilterSet):
    """`?activo=true&busqueda=perez`."""

    busqueda = filtros.CharFilter(method="filtrar_por_texto", label="Nombre o documento")

    class Meta:
        model = Cliente
        fields = ("activo", "tipo_documento")

    def filtrar_por_texto(self, consulta, nombre_del_campo, valor):
        """Nombre, apellido o documento: lo que quien busca tiene a mano."""
        return consulta.filter(
            Q(nombre__icontains=valor)
            | Q(apellido__icontains=valor)
            | Q(numero_documento__icontains=valor)
        )

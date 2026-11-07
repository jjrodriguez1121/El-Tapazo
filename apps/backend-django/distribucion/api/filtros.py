"""Filtros de los listados del canal mayorista."""

from django.db.models import Q
from django_filters import rest_framework as filtros

from distribucion.models import ClienteDistribucion, PedidoDistribucion


class ClienteDistribucionFiltro(filtros.FilterSet):
    """`?activo=true&busqueda=esquina`."""

    busqueda = filtros.CharFilter(method="filtrar_por_texto", label="Razón social o NIT")

    class Meta:
        model = ClienteDistribucion
        fields = ("activo", "ciudad")

    def filtrar_por_texto(self, consulta, nombre_del_campo, valor):
        """Razón social o NIT: lo que quien busca tiene a mano."""
        return consulta.filter(Q(razon_social__icontains=valor) | Q(nit__icontains=valor))


class PedidoDistribucionFiltro(filtros.FilterSet):
    """`?estado=en_ruta` es la consulta de la ruta: qué va en el camión hoy."""

    class Meta:
        model = PedidoDistribucion
        fields = ("estado", "cliente_distribucion", "usuario")

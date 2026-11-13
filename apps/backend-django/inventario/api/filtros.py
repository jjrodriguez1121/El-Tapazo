"""Filtros de los listados del inventario."""

from django_filters import rest_framework as filtros

from inventario.models import Existencia, MovimientoInventario


class ExistenciaFiltro(filtros.FilterSet):
    """`?ubicacion=2&producto=17`."""

    class Meta:
        model = Existencia
        fields = ("producto",)


class MovimientoFiltro(filtros.FilterSet):
    """`?producto=17&tipo=merma` — el kardex de un producto es la consulta estrella."""

    class Meta:
        model = MovimientoInventario
        fields = ("producto", "tipo", "referencia_tipo", "referencia_id")

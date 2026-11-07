"""Filtros de los listados del inventario."""

from django_filters import rest_framework as filtros

from inventario.models import Existencia, MovimientoInventario, Ubicacion


class UbicacionFiltro(filtros.FilterSet):
    class Meta:
        model = Ubicacion
        fields = ("activa", "tipo")


class ExistenciaFiltro(filtros.FilterSet):
    """`?ubicacion=2&producto=17`."""

    class Meta:
        model = Existencia
        fields = ("ubicacion", "producto")


class MovimientoFiltro(filtros.FilterSet):
    """`?producto=17&tipo=merma` — el kardex de un producto es la consulta estrella."""

    class Meta:
        model = MovimientoInventario
        fields = ("producto", "ubicacion", "tipo", "referencia_tipo", "referencia_id")

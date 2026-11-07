"""Filtros de los listados del evento/bar."""

from django_filters import rest_framework as filtros

from eventos.models import AlertaConsumo, ClienteEvento, Evento, GrupoEvento, PedidoEvento


class EventoFiltro(filtros.FilterSet):
    class Meta:
        model = Evento
        fields = ("estado", "ubicacion")


class GrupoFiltro(filtros.FilterSet):
    class Meta:
        model = GrupoEvento
        fields = ("evento", "estado")


class CuentaFiltro(filtros.FilterSet):
    """`?abiertas=true` es la consulta de la barra: quién sigue con cuenta."""

    abiertas = filtros.BooleanFilter(method="filtrar_abiertas", label="Solo cuentas abiertas")

    class Meta:
        model = ClienteEvento
        fields = ("grupo_evento", "cliente")

    def filtrar_abiertas(self, consulta, nombre_del_campo, valor):
        return consulta.filter(liberada_en__isnull=valor)


class PedidoFiltro(filtros.FilterSet):
    class Meta:
        model = PedidoEvento
        fields = ("evento", "cliente_evento", "estado", "mesero")


class AlertaFiltro(filtros.FilterSet):
    sin_atender = filtros.BooleanFilter(method="filtrar_sin_atender")

    class Meta:
        model = AlertaConsumo
        fields = ("cliente_evento",)

    def filtrar_sin_atender(self, consulta, nombre_del_campo, valor):
        return consulta.filter(atendida_en__isnull=valor)

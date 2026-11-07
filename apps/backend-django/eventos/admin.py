from django.contrib import admin

from .models import (
    AlertaConsumo,
    ClienteEvento,
    DetallePedidoEvento,
    DispositivoNfc,
    Evento,
    GrupoEvento,
    PagoEvento,
    PedidoEvento,
    PulseraNfc,
)


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "negocio", "ubicacion", "fecha_inicio", "fecha_fin", "estado")
    list_filter = ("negocio", "estado", "tipo_espacio")
    search_fields = ("nombre",)
    date_hierarchy = "fecha_inicio"


@admin.register(PulseraNfc)
class PulseraNfcAdmin(admin.ModelAdmin):
    list_display = ("uid_tag", "negocio", "estado")
    list_filter = ("negocio", "estado")
    search_fields = ("uid_tag",)


@admin.register(DispositivoNfc)
class DispositivoNfcAdmin(admin.ModelAdmin):
    """El token no se muestra: en la base solo está su hash, y es a propósito."""

    list_display = ("nombre", "negocio", "activo", "ultimo_uso_en")
    list_filter = ("negocio", "activo")
    search_fields = ("nombre",)
    readonly_fields = ("hash_token", "ultimo_uso_en")


@admin.register(GrupoEvento)
class GrupoEventoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "negocio", "evento", "mesa_zona", "estado", "cerrado_en")
    list_filter = ("negocio", "estado")
    search_fields = ("nombre_referencia", "mesa_zona")
    autocomplete_fields = ("evento", "abierto_por", "cerrado_por")


@admin.register(ClienteEvento)
class ClienteEventoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "negocio", "grupo_evento", "pulsera", "limite_alerta", "liberada_en")
    list_filter = ("negocio",)
    search_fields = ("cliente__nombre", "cliente__apellido", "pulsera__uid_tag")
    autocomplete_fields = ("grupo_evento", "cliente", "pulsera", "asignada_por", "liberada_por")


class DetallePedidoEventoInline(admin.TabularInline):
    """Las líneas se editan dentro de su comanda: solas no significan nada."""

    model = DetallePedidoEvento
    extra = 0
    autocomplete_fields = ("producto",)


@admin.register(PedidoEvento)
class PedidoEventoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "negocio", "evento", "cliente_evento", "mesero", "estado")
    list_filter = ("negocio", "estado")
    search_fields = ("id", "cliente_evento__cliente__nombre", "cliente_evento__cliente__apellido")
    autocomplete_fields = ("evento", "cliente_evento", "mesero")
    inlines = [DetallePedidoEventoInline]


@admin.register(DetallePedidoEvento)
class DetallePedidoEventoAdmin(admin.ModelAdmin):
    list_display = ("pedido_evento", "producto", "cantidad", "precio_unitario")
    list_filter = ("negocio",)
    search_fields = ("producto__nombre", "producto__sku")
    autocomplete_fields = ("pedido_evento", "producto")


@admin.register(AlertaConsumo)
class AlertaConsumoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente_evento",
        "negocio",
        "monto_acumulado",
        "umbral_superado",
        "atendida_en",
        "atendida_por",
    )
    list_filter = ("negocio",)
    date_hierarchy = "fecha"
    autocomplete_fields = ("cliente_evento", "atendida_por")


@admin.register(PagoEvento)
class PagoEventoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "negocio", "evento", "monto", "metodo", "recibido_por", "fecha")
    list_filter = ("negocio", "metodo")
    search_fields = ("referencia_transaccion",)
    date_hierarchy = "fecha"
    autocomplete_fields = (
        "evento",
        "grupo_evento",
        "cliente_evento",
        "pedido_evento",
        "recibido_por",
    )

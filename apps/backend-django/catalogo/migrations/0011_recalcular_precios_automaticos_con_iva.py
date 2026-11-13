from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def recalcular_precios_automaticos(apps, schema_editor):
    Producto = apps.get_model("catalogo", "Producto")
    productos = Producto.objects.filter(precio_venta_automatico=True).select_related("impuesto")

    for producto in productos.iterator():
        costo = Decimal(producto.costo or 0)
        margen = Decimal(producto.margen_ganancia or 0)
        porcentaje_iva = (
            Decimal(producto.impuesto.porcentaje) if producto.impuesto_id else Decimal("0")
        )
        precio_sin_iva = costo * (Decimal("1") + margen / Decimal("100"))
        producto.precio_venta = (
            precio_sin_iva * (Decimal("1") + porcentaje_iva / Decimal("100"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        producto.save(update_fields=["precio_venta"])


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0010_agregar_iva_cero"),
    ]

    operations = [
        migrations.RunPython(recalcular_precios_automaticos, migrations.RunPython.noop),
    ]

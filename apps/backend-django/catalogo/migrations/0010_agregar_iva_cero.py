from django.db import migrations


def agregar_iva_cero(apps, schema_editor):
    Impuesto = apps.get_model("catalogo", "Impuesto")
    Negocio = apps.get_model("negocios", "Negocio")
    for negocio in Negocio.objects.all():
        tarifas = (
            ("IVA 19 %", 19, "gravado"),
            ("IVA 5 %", 5, "gravado"),
            ("IVA 0 %", 0, "exento"),
            ("Exento", 0, "exento"),
            ("No gravado", 0, "no_gravado"),
        )
        for nombre, porcentaje, tratamiento in tarifas:
            Impuesto.objects.update_or_create(
                negocio_id=negocio.id,
                nombre=nombre,
                defaults={
                    "porcentaje": porcentaje,
                    "tipo_tratamiento": tratamiento,
                    "activo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0009_alter_producto_costo"),
        ("negocios", "0001_crear_negocios"),
    ]

    operations = [
        migrations.RunPython(agregar_iva_cero, migrations.RunPython.noop),
    ]

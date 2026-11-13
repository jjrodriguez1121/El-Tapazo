from django.db import migrations


def crear_impuestos_iniciales(apps, schema_editor):
    Impuesto = apps.get_model("catalogo", "Impuesto")
    Producto = apps.get_model("catalogo", "Producto")
    Negocio = apps.get_model("negocios", "Negocio")

    tarifas = (
        ("IVA 19 %", 19, "gravado"),
        ("IVA 5 %", 5, "gravado"),
        ("Exento", 0, "exento"),
        ("No gravado", 0, "no_gravado"),
    )

    for negocio in Negocio.objects.all():
        impuesto_iva_19 = None
        for nombre, porcentaje, tratamiento in tarifas:
            impuesto, _ = Impuesto.objects.get_or_create(
                negocio_id=negocio.id,
                nombre=nombre,
                defaults={
                    "porcentaje": porcentaje,
                    "tipo_tratamiento": tratamiento,
                    "activo": True,
                },
            )
            if nombre == "IVA 19 %":
                impuesto_iva_19 = impuesto

        Producto.objects.filter(
            negocio_id=negocio.id,
            impuesto_id__isnull=True,
        ).update(impuesto_id=impuesto_iva_19.id)


def eliminar_impuestos_iniciales(apps, schema_editor):
    Impuesto = apps.get_model("catalogo", "Impuesto")
    Impuesto.objects.filter(nombre__in=("IVA 19 %", "IVA 5 %", "Exento", "No gravado")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0005_producto_codigo_producto_contenido_presentacion_and_more"),
        ("negocios", "0001_crear_negocios"),
    ]

    operations = [
        migrations.RunPython(crear_impuestos_iniciales, eliminar_impuestos_iniciales),
    ]

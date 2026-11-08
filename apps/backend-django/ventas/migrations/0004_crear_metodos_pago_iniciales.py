from django.db import migrations


def crear_metodos_pago(apps, schema_editor):
    Negocio = apps.get_model("negocios", "Negocio")
    MetodoPago = apps.get_model("ventas", "MetodoPago")
    for negocio in Negocio.objects.all():
        for nombre in ("Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"):
            MetodoPago.objects.get_or_create(
                negocio_id=negocio.id,
                nombre=nombre,
                defaults={"estado": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0001_crear_negocios"),
        ("ventas", "0003_detalleventa_base_gravable_and_more"),
    ]

    operations = [
        migrations.RunPython(crear_metodos_pago, migrations.RunPython.noop),
    ]

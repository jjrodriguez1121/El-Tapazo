from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0007_producto_precio_automatico"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="producto",
            name="proveedores",
        ),
        migrations.DeleteModel(
            name="ProductoProveedor",
        ),
    ]

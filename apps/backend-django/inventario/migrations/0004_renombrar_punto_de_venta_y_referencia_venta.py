from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inventario", "0003_agregar_cantidad_minima_a_existencias")]

    operations = [
        migrations.AlterField(
            model_name="ubicacion",
            name="tipo",
            field=models.CharField(
                choices=[("bodega", "Bodega"), ("punto_de_venta", "Punto de venta")],
                default="bodega",
                max_length=30,
                verbose_name="tipo",
            ),
        ),
        migrations.AlterField(
            model_name="movimientoinventario",
            name="referencia_tipo",
            field=models.CharField(
                choices=[
                    ("venta", "Venta"),
                    ("compra", "Compra a proveedor"),
                    ("traslado", "Traslado entre ubicaciones"),
                    ("ajuste", "Ajuste manual"),
                ],
                max_length=30,
                verbose_name="tipo de referencia",
            ),
        ),
    ]

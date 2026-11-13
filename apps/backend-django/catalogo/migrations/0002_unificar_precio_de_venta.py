from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalogo", "0001_crear_catalogo")]

    operations = [
        migrations.RemoveConstraint(model_name="producto", name="producto_precios_no_negativos"),
        migrations.RemoveField(model_name="producto", name="precio_evento"),
        migrations.RemoveField(model_name="producto", name="precio_mayorista"),
        migrations.AddField(
            model_name="producto",
            name="precio_venta",
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name="precio de venta"),
        ),
        migrations.AddConstraint(
            model_name="producto",
            constraint=models.CheckConstraint(
                condition=models.Q(("costo__gte", 0), ("precio_venta__gte", 0)),
                name="producto_precios_no_negativos",
                violation_error_message="Ni el costo ni el precio de venta pueden ser negativos.",
            ),
        ),
    ]

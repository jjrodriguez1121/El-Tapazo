from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0006_datos_iniciales_impuestos"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="margen_ganancia",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("30.00"),
                max_digits=6,
                verbose_name="margen de ganancia",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="precio_venta_automatico",
            field=models.BooleanField(
                default=True,
                verbose_name="precio de venta automático",
            ),
        ),
    ]

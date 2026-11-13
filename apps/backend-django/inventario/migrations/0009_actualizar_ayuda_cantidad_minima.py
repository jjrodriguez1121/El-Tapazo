from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0008_existencia_cantidad_actual"),
    ]

    operations = [
        migrations.AlterField(
            model_name="existencia",
            name="cantidad_minima",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Por debajo de esto hay que reponer; 0 desactiva el mínimo, no la alerta por agotado.",
                max_digits=12,
                verbose_name="cantidad mínima",
            ),
        ),
    ]

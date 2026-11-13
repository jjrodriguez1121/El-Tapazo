from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ventas", "0006_estado_de_entrega_y_cartera_anulada")]

    operations = [
        migrations.AddField(
            model_name="pagoventa",
            name="estado",
            field=models.CharField(
                choices=[("CONFIRMADO", "Confirmado"), ("ANULADO", "Anulado")],
                default="CONFIRMADO",
                max_length=10,
                verbose_name="estado",
            ),
        ),
    ]

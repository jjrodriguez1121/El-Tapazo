from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ventas", "0004_crear_metodos_pago_iniciales")]

    operations = [
        migrations.RemoveConstraint(
            model_name="venta",
            name="venta_estado_coherente_con_pago",
        ),
        migrations.AddConstraint(
            model_name="venta",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(tipo_pago="contado", estado="pagada")
                    | models.Q(tipo_pago="credito", estado="pendiente")
                    | models.Q(tipo_pago="credito", estado="pagada")
                    | models.Q(estado="anulada")
                ),
                name="venta_estado_coherente_con_pago",
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ventas", "0005_permitir_venta_credito_pagada")]

    operations = [
        migrations.AddField(
            model_name="venta",
            name="estado_entrega",
            field=models.CharField(
                choices=[
                    ("pendiente_entrega", "Pendiente de entrega"),
                    ("entregada", "Entregada"),
                    ("anulada", "Anulada"),
                ],
                default="pendiente_entrega",
                max_length=20,
                verbose_name="estado de entrega",
            ),
        ),
        migrations.AlterField(
            model_name="cuentaporcobrar",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("parcial", "Abonada parcialmente"),
                    ("pagada", "Pagada"),
                    ("vencida", "Vencida"),
                    ("anulada", "Anulada"),
                ],
                default="pendiente",
                max_length=10,
                verbose_name="estado",
            ),
        ),
    ]

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0003_cliente_direccion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cliente",
            name="tipo_documento",
            field=models.CharField(
                choices=[
                    ("cedula", "Cédula de ciudadanía"),
                    ("cedula_extranjeria", "Cédula de extranjería"),
                    ("pasaporte", "Pasaporte"),
                    ("tarjeta_identidad", "Tarjeta de identidad"),
                    ("nit", "NIT"),
                ],
                default="cedula",
                max_length=25,
                verbose_name="tipo de documento",
            ),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="apellido",
            field=models.CharField(blank=True, max_length=120, verbose_name="apellido"),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="fecha_nacimiento",
            field=models.DateField(
                blank=True,
                help_text="Se guarda la fecha y no la edad: la edad cambia sola cada año.",
                null=True,
                verbose_name="fecha de nacimiento",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="cliente",
            name="cliente_fecha_nacimiento_razonable",
        ),
        migrations.AddConstraint(
            model_name="cliente",
            constraint=models.CheckConstraint(
                condition=models.Q(("fecha_nacimiento__isnull", True))
                | models.Q(("fecha_nacimiento__gt", datetime.date(1900, 1, 1))),
                name="cliente_fecha_nacimiento_razonable",
                violation_error_message="La fecha de nacimiento no es válida.",
            ),
        ),
    ]

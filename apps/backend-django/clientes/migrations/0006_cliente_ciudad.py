from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0005_alter_cliente_cliente_fecha_nacimiento_razonable"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="ciudad",
            field=models.CharField(blank=True, max_length=100, verbose_name="ciudad"),
        ),
    ]

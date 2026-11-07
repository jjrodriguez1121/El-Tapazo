import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogo", "0002_unificar_precio_de_venta"),
        ("clientes", "0002_agregar_indice_de_busqueda_por_nombre"),
        ("inventario", "0004_renombrar_punto_de_venta_y_referencia_venta"),
        ("negocios", "0001_crear_negocios"),
    ]

    operations = [
        migrations.CreateModel(
            name="Venta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
                ("tipo_pago", models.CharField(choices=[("contado", "Contado"), ("credito", "Crédito")], max_length=10, verbose_name="tipo de pago")),
                ("estado", models.CharField(choices=[("pagada", "Pagada"), ("pendiente", "Pendiente de cobro"), ("anulada", "Anulada")], max_length=12, verbose_name="estado")),
                ("fecha", models.DateTimeField(default=timezone.now, verbose_name="fecha")),
                ("observaciones", models.TextField(blank=True, verbose_name="observaciones")),
                ("cliente", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ventas", to="clientes.cliente", verbose_name="cliente")),
                ("negocio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="%(class)ss", to="negocios.negocio", verbose_name="negocio")),
                ("ubicacion", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ventas", to="inventario.ubicacion", verbose_name="ubicación")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ventas_registradas", to=settings.AUTH_USER_MODEL, verbose_name="vendedor")),
            ],
            options={"db_table": "ventas", "ordering": ["-fecha"]},
        ),
        migrations.CreateModel(
            name="DetalleVenta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
                ("cantidad", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="cantidad")),
                ("precio_unitario", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="precio unitario")),
                ("negocio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="%(class)ss", to="negocios.negocio", verbose_name="negocio")),
                ("producto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="detalles_venta", to="catalogo.producto", verbose_name="producto")),
                ("venta", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detalles", to="ventas.venta", verbose_name="venta")),
            ],
            options={"db_table": "detalles_venta"},
        ),
        migrations.CreateModel(
            name="CuentaPorCobrar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
                ("fecha_vencimiento", models.DateField(verbose_name="fecha de vencimiento")),
                ("total", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="total")),
                ("saldo", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="saldo")),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("parcial", "Abonada parcialmente"), ("pagada", "Pagada"), ("vencida", "Vencida")], default="pendiente", max_length=10, verbose_name="estado")),
                ("negocio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="%(class)ss", to="negocios.negocio", verbose_name="negocio")),
                ("venta", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="cuenta_por_cobrar", to="ventas.venta", verbose_name="venta")),
            ],
            options={"db_table": "cuentas_por_cobrar", "ordering": ["fecha_vencimiento"]},
        ),
        migrations.CreateModel(
            name="PagoVenta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
                ("monto", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="monto")),
                ("metodo", models.CharField(choices=[("efectivo", "Efectivo"), ("tarjeta", "Tarjeta"), ("nequi", "Nequi"), ("transferencia", "Transferencia"), ("otro", "Otro")], max_length=20, verbose_name="medio de pago")),
                ("referencia_transaccion", models.CharField(blank=True, max_length=100, verbose_name="referencia")),
                ("fecha", models.DateTimeField(default=timezone.now, verbose_name="fecha")),
                ("cuenta_por_cobrar", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="abonos", to="ventas.cuentaporcobrar", verbose_name="cuenta por cobrar")),
                ("negocio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="%(class)ss", to="negocios.negocio", verbose_name="negocio")),
                ("recibido_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pagos_recibidos", to=settings.AUTH_USER_MODEL, verbose_name="recibido por")),
                ("venta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pagos", to="ventas.venta", verbose_name="venta")),
            ],
            options={"db_table": "pagos_venta", "ordering": ["-fecha"]},
        ),
        migrations.AddConstraint(model_name="venta", constraint=models.CheckConstraint(condition=models.Q(("tipo_pago", "contado"), ("estado", "pagada")) | models.Q(("tipo_pago", "credito"), ("estado", "pendiente")) | models.Q(("estado", "anulada")), name="venta_estado_coherente_con_pago")),
        migrations.AddConstraint(model_name="detalleventa", constraint=models.UniqueConstraint(fields=("venta", "producto"), name="detalle_venta_producto_unico")),
        migrations.AddConstraint(model_name="detalleventa", constraint=models.CheckConstraint(condition=models.Q(("cantidad__gt", 0)), name="detalle_venta_cantidad_positiva")),
        migrations.AddConstraint(model_name="detalleventa", constraint=models.CheckConstraint(condition=models.Q(("precio_unitario__gte", 0)), name="detalle_venta_precio_no_negativo")),
        migrations.AddConstraint(model_name="cuentaporcobrar", constraint=models.CheckConstraint(condition=models.Q(("total__gt", 0)), name="cuenta_total_positivo")),
        migrations.AddConstraint(model_name="cuentaporcobrar", constraint=models.CheckConstraint(condition=models.Q(("saldo__gte", 0)), name="cuenta_saldo_no_negativo")),
        migrations.AddConstraint(model_name="cuentaporcobrar", constraint=models.CheckConstraint(condition=models.Q(("saldo__lte", models.F("total"))), name="cuenta_saldo_no_supera_total")),
        migrations.AddConstraint(model_name="pagoventa", constraint=models.CheckConstraint(condition=models.Q(("monto__gt", 0)), name="pago_venta_monto_positivo")),
    ]

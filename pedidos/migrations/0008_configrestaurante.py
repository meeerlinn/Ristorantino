from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0007_add_fecha_cierre_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionRestaurante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(default='Ristorantino', max_length=200)),
                ('ruc', models.CharField(blank=True, max_length=30)),
                ('direccion', models.CharField(blank=True, max_length=300)),
                ('telefono', models.CharField(blank=True, max_length=50)),
                ('tasa_iva', models.IntegerField(default=10)),
            ],
            options={
                'db_table': 'config_restaurante',
            },
        ),
    ]

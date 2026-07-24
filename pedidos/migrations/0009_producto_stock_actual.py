from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0008_configrestaurante'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='stock_actual',
            field=models.IntegerField(
                blank=True,
                default=None,
                null=True,
                help_text='Unidades en stock. Vacío = sin límite (no se controla).',
            ),
        ),
    ]

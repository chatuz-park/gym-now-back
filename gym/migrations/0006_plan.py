from django.db import migrations, models


def seed_default_plans(apps, schema_editor):
    Plan = apps.get_model('gym', 'Plan')
    defaults = [
        {
            'slug': 'standard',
            'name': 'Estándar',
            'description': 'Acceso básico al gimnasio',
            'price': 199000,
            'duration_days': 30,
            'features': ['Acceso básico', '2 rutinas', 'Seguimiento básico'],
            'color': 'blue',
            'is_active': True,
        },
        {
            'slug': 'premium',
            'name': 'Premium',
            'description': 'Acceso completo y seguimiento avanzado',
            'price': 299000,
            'duration_days': 30,
            'features': [
                'Acceso completo',
                'Rutinas ilimitadas',
                'Seguimiento avanzado',
                'Consultas prioritarias',
            ],
            'color': 'purple',
            'is_active': True,
        },
        {
            'slug': 'personalized',
            'name': 'Personalizada',
            'description': 'Plan premium con sesiones 1:1 y nutrición',
            'price': 399000,
            'duration_days': 30,
            'features': [
                'Todo de Premium',
                'Rutinas personalizadas',
                'Sesiones 1:1',
                'Nutrición incluida',
            ],
            'color': 'green',
            'is_active': True,
        },
    ]
    for data in defaults:
        Plan.objects.get_or_create(slug=data['slug'], defaults=data)


def unseed_default_plans(apps, schema_editor):
    Plan = apps.get_model('gym', 'Plan')
    Plan.objects.filter(slug__in=['standard', 'premium', 'personalized']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0005_customuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, default='')),
                ('price', models.PositiveIntegerField(help_text='Precio en COP')),
                ('duration_days', models.PositiveIntegerField(default=30)),
                ('features', models.JSONField(default=list)),
                ('color', models.CharField(
                    choices=[
                        ('blue', 'Azul'),
                        ('purple', 'Morado'),
                        ('green', 'Verde'),
                        ('orange', 'Naranja'),
                        ('red', 'Rojo'),
                        ('gray', 'Gris'),
                    ],
                    default='blue',
                    max_length=20,
                )),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Plan',
                'verbose_name_plural': 'Planes',
                'ordering': ['price', 'name'],
            },
        ),
        migrations.AlterField(
            model_name='client',
            name='subscription_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.RunPython(seed_default_plans, unseed_default_plans),
    ]

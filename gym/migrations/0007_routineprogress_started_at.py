from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0006_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='routineprogress',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

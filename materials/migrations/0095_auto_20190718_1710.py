# Generated by Django 2.2.1 on 2019-07-18 21:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('materials', '0094_auto_20190718_1358'),
    ]

    operations = [
        migrations.AddField(
            model_name='numericalvaluefixed',
            name='upper_bound',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='phasetransition',
            name='upper_bound',
            field=models.FloatField(null=True),
        ),
        migrations.CreateModel(
            name='UpperBound',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('numerical_value', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='materials.NumericalValue')),
                ('value', models.FloatField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_upperbound_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_upperbound_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

# Generated by Django 3.1.12 on 2022-03-08 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0105_auto_20210610_1030'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='derived_to_from',
            field=models.ManyToManyField(blank=True, related_name='_system_derived_to_from_+', to='materials.System'),
        ),
    ]

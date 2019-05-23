# Generated by Django 2.2.1 on 2019-05-23 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0086_auto_20190523_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='sample_type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'single crystal'), (1, 'powder'), (2, 'film'), (3, 'bulk polycrystalline'), (4, 'pellet'), (5, 'nanoform'), (6, 'unknown')]),
        ),
    ]

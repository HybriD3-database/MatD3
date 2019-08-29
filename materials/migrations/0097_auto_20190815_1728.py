# Generated by Django 2.2.1 on 2019-08-15 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0096_dataset_verified_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='dimensionality',
            field=models.PositiveSmallIntegerField(choices=[(3, 3), (2, 2), (1, 1), (0, 0)]),
        ),
    ]
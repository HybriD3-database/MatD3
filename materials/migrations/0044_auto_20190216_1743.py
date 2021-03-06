# Generated by Django 2.0.1 on 2019-02-16 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0043_auto_20190216_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='comment',
            field=models.TextField(default='', max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='dimensionality',
            field=models.PositiveSmallIntegerField(choices=[(2, 2), (3, 3)], default=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='experimental',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='has_files',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]

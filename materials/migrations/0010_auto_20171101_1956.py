# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-01 19:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0009_auto_20171101_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='atomicpositions',
            name='phase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='materials.Phase'),
        ),
        migrations.AlterField(
            model_name='atomicpositions',
            name='system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='materials.System'),
        ),
        migrations.AlterField(
            model_name='atomicpositions',
            name='temperature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='materials.Temperature'),
        ),
    ]

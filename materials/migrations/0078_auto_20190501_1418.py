# Generated by Django 2.1.7 on 2019-05-01 18:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0077_auto_20190430_1154'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataset',
            old_name='plotted',
            new_name='is_figure',
        ),
    ]

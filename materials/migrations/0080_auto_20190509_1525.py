# Generated by Django 2.1.7 on 2019-05-09 19:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0079_remove_property_require_input_files'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bandstructure',
            name='idinfo_ptr',
        ),
        migrations.RemoveField(
            model_name='bandstructure',
            name='synthesis_method',
        ),
        migrations.RemoveField(
            model_name='bandstructure',
            name='system',
        ),
        migrations.DeleteModel(
            name='BandStructure',
        ),
    ]

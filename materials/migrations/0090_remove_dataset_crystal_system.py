# Generated by Django 2.2.1 on 2019-06-05 20:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0089_subset_crystal_system'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='crystal_system',
        ),
    ]

# Generated by Django 2.2.1 on 2019-05-21 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0082_auto_20190520_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='primary_property_label',
            field=models.TextField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='dataset',
            name='secondary_property_label',
            field=models.TextField(blank=True, max_length=50),
        ),
    ]

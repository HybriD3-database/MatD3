# Generated by Django 2.2.1 on 2019-05-22 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0083_auto_20190521_1322'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='numericalvaluefixed',
            name='dataset',
        ),
        migrations.AddField(
            model_name='dataset',
            name='linked_to',
            field=models.ManyToManyField(related_name='_dataset_linked_to_+', to='materials.Dataset'),
        ),
    ]

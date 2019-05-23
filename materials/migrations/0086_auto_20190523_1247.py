# Generated by Django 2.2.1 on 2019-05-23 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0085_auto_20190523_1107'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ExcitonEmission',
        ),
        migrations.RemoveField(
            model_name='synthesismethodold',
            name='idinfo_ptr',
        ),
        migrations.RemoveField(
            model_name='synthesismethodold',
            name='system',
        ),
        migrations.DeleteModel(
            name='SynthesisMethodOld',
        ),
        migrations.RemoveField(
            model_name='idinfo',
            name='contributor',
        ),
        migrations.RemoveField(
            model_name='idinfo',
            name='method',
        ),
        migrations.RemoveField(
            model_name='idinfo',
            name='phase',
        ),
        migrations.RemoveField(
            model_name='idinfo',
            name='reference',
        ),
        migrations.RemoveField(
            model_name='idinfo',
            name='specific_method',
        ),
        migrations.DeleteModel(
            name='IDInfo',
        ),
        migrations.DeleteModel(
            name='Method',
        ),
        migrations.DeleteModel(
            name='Phase',
        ),
        migrations.DeleteModel(
            name='SpecificMethod',
        ),
    ]

# Generated by Django 2.2.1 on 2019-08-20 19:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import materials.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('materials', '0097_auto_20190815_1728'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DatasetFile',
            new_name='AdditionalFile',
        ),
        migrations.CreateModel(
            name='InputDataFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('dataset_file', models.FileField(upload_to=materials.models.data_file_path)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_inputdatafile_created_by', to=settings.AUTH_USER_MODEL)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='input_files', to='materials.Dataset')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_inputdatafile_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='additionalfile',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_additionalfile_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='additionalfile',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials_additionalfile_updated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]

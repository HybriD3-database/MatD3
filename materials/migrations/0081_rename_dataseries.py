from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('materials', '0080_auto_20190509_1525'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Dataseries',
            new_name='Subset',
        ),
    ]

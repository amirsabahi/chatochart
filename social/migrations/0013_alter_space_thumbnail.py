# Generated by Django 4.0.2 on 2022-02-21 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0012_alter_space_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='space',
            name='thumbnail',
            field=models.FilePathField(default='/', path=None),
        ),
    ]

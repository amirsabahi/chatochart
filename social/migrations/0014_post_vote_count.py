# Generated by Django 4.0.2 on 2022-02-22 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0013_alter_space_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='vote_count',
            field=models.IntegerField(default=0),
        ),
    ]

# Generated by Django 4.0.2 on 2022-03-08 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0025_comment_depth_alter_post_comment_depth'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='lft',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='comment',
            name='rgt',
            field=models.PositiveIntegerField(default=2),
        ),
    ]
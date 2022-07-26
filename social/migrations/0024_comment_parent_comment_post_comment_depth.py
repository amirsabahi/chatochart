# Generated by Django 4.0.2 on 2022-03-06 12:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0023_bookmarks_deleted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='parent_comment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='post_parent_comment', to='social.comment'),
        ),
        migrations.AddField(
            model_name='post',
            name='comment_depth',
            field=models.PositiveIntegerField(default=0, null=True),
        ),
    ]
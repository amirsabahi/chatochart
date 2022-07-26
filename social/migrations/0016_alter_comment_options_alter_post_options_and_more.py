# Generated by Django 4.0.2 on 2022-03-04 08:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('social', '0015_spacepolicy'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created_at',)},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-created_at',)},
        ),
        migrations.AddField(
            model_name='space',
            name='user_can_post',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.CreateModel(
            name='Bookmarks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_bookmarked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_bookmarked', to='social.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmark', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verb', models.CharField(choices=[('PTC', 'Post to Channel'), ('COP', 'Comment on post'), ('COC', 'COC'), ('VGU', 'Gained a vote up')], max_length=3)),
                ('target_id', models.PositiveIntegerField(blank=True, null=True)),
                ('edge_rank', models.PositiveIntegerField(default=0)),
                ('parent_type', models.CharField(blank=True, choices=[('P', 'Post'), ('C', 'Comment'), ('V', 'V')], max_length=1, null=True)),
                ('is_notification', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_space', to='social.space')),
                ('target_content', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_obj', to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
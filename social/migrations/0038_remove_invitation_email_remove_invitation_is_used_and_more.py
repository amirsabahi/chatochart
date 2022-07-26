# Generated by Django 4.0.2 on 2022-04-11 17:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0037_alter_space_thumbnail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='email',
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='is_used',
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='unique_code',
        ),
        migrations.AddField(
            model_name='invitation',
            name='invitee_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='invitee_user', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='invitation_code',
            field=models.CharField(default=None, max_length=150, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='invitation_counter_default',
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='user',
            name='invited_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invited_by_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='user',
            name='invitation_counter',
            field=models.PositiveSmallIntegerField(default=50),
        ),
    ]
# Generated by Django 4.0.2 on 2022-04-12 11:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0038_remove_invitation_email_remove_invitation_is_used_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invitation',
            old_name='invitee_id',
            new_name='invitee',
        ),
        migrations.RenameField(
            model_name='invitation',
            old_name='invitor_id',
            new_name='invitor',
        ),
    ]
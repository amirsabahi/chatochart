# Generated by Django 4.0.2 on 2022-03-18 07:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0032_remove_post_vote_count_post_total_votes_down_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vote',
            name='created_by',
        ),
    ]
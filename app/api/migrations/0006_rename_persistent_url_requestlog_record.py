# Generated by Django 4.0 on 2022-06-01 19:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_requestlog_referer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requestlog',
            old_name='persistent_url',
            new_name='record',
        ),
    ]

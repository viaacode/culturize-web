# Generated by Django 4.0 on 2022-05-30 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_requestlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestlog',
            name='referer',
            field=models.CharField(max_length=100, null=True),
        ),
    ]

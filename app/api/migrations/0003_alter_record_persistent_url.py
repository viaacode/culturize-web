# Generated by Django 4.0 on 2022-05-30 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_record_alter_item_unique_together_remove_item_domain_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='persistent_url',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]

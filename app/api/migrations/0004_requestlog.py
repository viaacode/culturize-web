# Generated by Django 4.0 on 2022-05-30 20:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_record_persistent_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('referer', models.CharField(max_length=100)),
                ('persistent_url', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.record')),
            ],
        ),
    ]

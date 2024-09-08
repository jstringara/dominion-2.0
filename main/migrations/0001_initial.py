# Generated by Django 3.2.9 on 2021-12-02 11:58

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('N', models.IntegerField()),
                ('tour_id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
    ]
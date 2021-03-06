# Generated by Django 3.2.9 on 2021-12-10 17:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0005_auto_20211208_0223'),
    ]

    operations = [
        migrations.CreateModel(
            name='Albo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('player_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('tour_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.metadata')),
            ],
        ),
    ]

# Generated by Django 3.2.9 on 2021-12-02 22:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0003_constant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Elo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('elo', models.FloatField(default=1500)),
                ('player_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('tour_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.metadata')),
            ],
        ),
    ]
# Generated by Django 5.1 on 2024-09-02 23:01

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0006_albo"),
    ]

    operations = [
        migrations.RenameField(
            model_name="albo",
            old_name="player_id",
            new_name="player",
        ),
        migrations.RenameField(
            model_name="albo",
            old_name="tour_id",
            new_name="tournament",
        ),
        migrations.RenameField(
            model_name="elo",
            old_name="player_id",
            new_name="player",
        ),
        migrations.RenameField(
            model_name="elo",
            old_name="tour_id",
            new_name="tournament",
        ),
        migrations.RenameField(
            model_name="game",
            old_name="tour_id",
            new_name="tournament",
        ),
    ]
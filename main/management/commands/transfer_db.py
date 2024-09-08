from django.core.management.base import BaseCommand
from main.models import Season, Tournament, Match, Result, EloScore  # new models
from main.models import Metadata, Game, EloOld  # old models

from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Transfer data from old models to new models"

    def handle(self, *args, **kwargs):
        # Create a new Season object
        season = Season.objects.create(name="Season 1", is_current=True)

        # Loop through all the Metadata objects
        for metadata in Metadata.objects.all():
            # Create a new Tournament object for each Metadata object
            tournament = Tournament.objects.create(
                datetime=metadata.date, season=season
            )

            # For all EloOld objects with tournament = metadata, create a new EloScore object
            for elo_old in EloOld.objects.filter(tournament=metadata):
                EloScore.objects.create(
                    player=elo_old.player,
                    elo=elo_old.elo,
                    tournament=tournament,
                )

            # Loop through all the Game objects
            for game in Game.objects.filter(tournament=metadata):
                # Create a new Match object for each Game object
                match = Match.objects.create(tournament=tournament)

                # Create a new Result object for player 1
                Result.objects.create(
                    match=match,
                    player=game.player_id_1,
                    num_turns=game.turns_1,
                    num_points=game.points_1,
                )

                # Create a new Result object for player 2
                Result.objects.create(
                    match=match,
                    player=game.player_id_2,
                    num_turns=game.turns_2,
                    num_points=game.points_2,
                )

        self.stdout.write(self.style.SUCCESS("Data transfer complete."))

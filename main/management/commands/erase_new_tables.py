from django.core.management.base import BaseCommand
from main.models import Season, Tournament, Match, Result, EloScore  # new models
from main.models import Metadata, Game, EloOld  # old models

from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Transfer data from old models to new models"

    def handle(self, *args, **kwargs):
        # Erase all the content in the new models
        Season.objects.all().delete()
        Tournament.objects.all().delete()
        Match.objects.all().delete()
        Result.objects.all().delete()
        EloScore.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Data transfer complete."))

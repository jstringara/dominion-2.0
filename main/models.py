from django.db import models
from django.conf import settings
from django.utils.timezone import now


class Season(models.Model):
    name = models.CharField(max_length=100)
    is_current = models.BooleanField(default=False)


class Tournament(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=now)


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)


class Result(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    num_turns = models.IntegerField(null=True)
    num_points = models.IntegerField(null=True)


class EloScore(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    elo = models.FloatField()
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)


class Parameter(models.Model):
    k = models.IntegerField(default=20)

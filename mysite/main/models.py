from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Metadata(models.Model):

    date = models.DateTimeField(default=now)
    N = models.IntegerField()
    tour_id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.date.strftime('%a %d-%m-%y (%H:%M)')


class Game(models.Model):

    player_id_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_1')
    points_1 = models.IntegerField(null=True, blank=True)
    turns_1 = models.IntegerField(null=True, blank=True)
    player_id_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_2')
    points_2 = models.IntegerField(null=True, blank=True)
    turns_2 = models.IntegerField(null=True, blank=True)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.player_id_1)+', '+str(self.player_id_2)+', '+str(self.tour_id)

class Constant(models.Model):
    k = models.IntegerField(default=20)

class Elo(models.Model):

    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    elo = models.FloatField(default=1500)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.player_id)+', '+str(self.tour_id)

#classi per le views, che alla fine ho scelto di non usare perchè fan solo casino
#class All_Combos(models.Model):
#  first_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='first_id')
#  second_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='second_id')
#  tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
#
#  class Meta:
#    managed=False
#class Every_Game(models.Model):
#  player_id_1 = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='game_player_id_1')
#  points_1 = models.IntegerField()
#  turns_1 = models.IntegerField()
#  player_id_2 = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='game_player_id_2')
#  points_2 = models.IntegerField()
#  turns_2 = models.IntegerField()
#  tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
#
#  class Meta:
#    managed=False
#class Outcome(models.Model):
#  player_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='outcome_player_id')
#  opponent_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='outcome_opponent_id')
#  outcome = models.DecimalField(max_digits=5, decimal_places=2)
#  tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
#
#  class Meta:
#    managed=False
#class Total_Outcome(models.Model):
#  player_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
#  total = models.DecimalField(max_digits=5, decimal_places=2)
#  tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
#
#  class Meta:
#    managed=False
#class Presence(models.Model):
#  player_id = models.ForeignKey(
#      settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
#  tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
#  presence = models.BooleanField()
#
#  class Meta:
#    managed=False
#

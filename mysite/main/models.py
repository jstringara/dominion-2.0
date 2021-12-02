from django.db import models
from view_table.models import ViewTable
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Metadata(models.Model):
    date = models.DateTimeField(default=now)
    N = models.IntegerField()
    tour_id = models.AutoField(primary_key=True)


class Game(models.Model):
    player_id_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_1')
    points_1 = models.IntegerField()
    turns_1 = models.IntegerField()
    player_id_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_2')
    points_2 = models.IntegerField()
    turns_2 = models.IntegerField()
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

class Constant(models.Model):
    k = models.IntegerField(default=20)

class All_Combos(ViewTable):
    first_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='first_id')
    second_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='second_id')
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    @classmethod
    def get_query(self):
        return '''SELECT 
"first"."id" as first_id,
"second"."id" as second_id,
"main_metadata"."tour_id" as tour_id
FROM 
    "auth_user" as first
CROSS JOIN
    "main_metadata"
CROSS JOIN
    "auth_user" as second
WHERE
    "first"."id" < "second"."id"
    AND
    "tour_id" <> 1'''

class Every_Game(ViewTable):
    player_id_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='game_player_id_1')
    points_1 = models.IntegerField()
    turns_1 = models.IntegerField()
    player_id_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='game_player_id_2')
    points_2 = models.IntegerField()
    turns_2 = models.IntegerField()
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    @classmethod
    def get_query(self):
        return '''SELECT
main_all_combos.first_id as player_id_1,
CASE
  WHEN main_all_combos.first_id = main_game.player_id_1_id
  THEN main_game.points_1
  ELSE main_game.points_2
END points_1,
CASE
  WHEN main_all_combos.first_id = main_game.player_id_1_id
  THEN main_game.turns_1
  ELSE main_game.turns_2
END turns_1,
main_all_combos.second_id as player_id_2,
CASE
  WHEN main_all_combos.second_id = main_game.player_id_1_id
  THEN main_game.points_1
  ELSE main_game.points_2
END points_2,
CASE
  WHEN main_all_combos.first_id = main_game.player_id_1_id
  THEN main_game.turns_1
  ELSE main_game.turns_2
END turns_2,
main_all_combos.tour_id as tour_id
FrOM
  main_all_combos
LEFT OUTER JOIN
  main_game
ON
  (
    (main_all_combos.first_id = main_game.player_id_1_id AND main_all_combos.second_id = main_game.player_id_2_id)
    OR
    (main_all_combos.first_id = main_game.player_id_2_id AND main_all_combos.second_id = main_game.player_id_1_id)
  )
  AND
  main_all_combos.tour_id = main_game.tour_id_id
'''

class Outcome(ViewTable):
    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='outcome_player_id')
    opponent_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='outcome_opponent_id')
    outcome = models.DecimalField(max_digits=5, decimal_places=2)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    @classmethod
    def get_query(self):
        return '''SELECT
auth_user.id as player_id,
CASE
    WHEN auth_user.id = main_every_game.player_id_1 THEN main_every_game.player_id_2
    ELSE main_every_game.player_id_1
END opponent_id,
CASE
  WHEN auth_user.id = main_every_game.player_id_1 THEN
    (main_every_game.points_1>main_every_game.points_2)+(main_every_game.points_1=main_every_game.points_2)*(main_every_game.turns_1<main_every_game.turns_2)+0.5*(main_every_game.points_1=main_every_game.points_2)*(main_every_game.turns_1=main_every_game.turns_2)
  ELSE
    (main_every_game.points_2>main_every_game.points_1)+(main_every_game.points_2=main_every_game.points_1)*(main_every_game.turns_2<main_every_game.turns_1)+0.5*(main_every_game.points_2=main_every_game.points_1)*(main_every_game.turns_2=main_every_game.turns_1)
END as outcome,
  main_every_game.tour_id as tour_id
FROM
  auth_user
INNER JOIN main_every_game ON main_every_game.player_id_1 = auth_user.id
OR main_every_game.player_id_2 = auth_user.id
'''

class Total_Outcome(ViewTable):
    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    total = models.DecimalField(max_digits=5, decimal_places=2)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    @classmethod
    def get_query(self):
        return'''SELECT
main_outcome.player_id as player_id,
SUM(main_outcome.outcome) as total,
main_outcome.tour_id as tour_id
FROM
    main_outcome
GROUP BY
    main_outcome.player_id, main_outcome.tour_id
'''

class Presence(ViewTable):
    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    presence = models.BooleanField()

    @classmethod
    def get_query(self):
        return '''SELECT
player_id,
CASE
    WHEN total IS NOT NULL THEN 1
    ELSE 0
END AS presence,
tour_id
FROM main_total_outcome
'''



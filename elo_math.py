# This file contains mathematical parts related to the Elo computation.
# For details see this: http://www.glicko.net/research/acjpaper.pdf


def get_expected_score(player_rating, opponent_rating):
    """
    Calculate the expected score of a player against an opponent.
    See formula (1) in the linked paper.
    """
    return 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))


def get_updated_rating(player_rating, expected_score, actual_score, k):
    """
    Calculate the updated score of a player.
    See formula (2) in the linked paper.
    """
    return player_rating + k * (actual_score - expected_score)

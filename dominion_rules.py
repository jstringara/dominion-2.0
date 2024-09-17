def calculate_match_outcome(
    num_points_current,
    num_turns_current,
    num_points_opponent,
    num_turns_opponent,
):
    """
    Function that calculates the outcome of a match for the current player against
    the opponent player.
    """

    # case in which the game is not finished
    if num_points_current is None and num_points_opponent is None:
        return 0

    if num_points_current > num_points_opponent:
        return 1
    elif num_points_current < num_points_opponent:
        return 0
    elif num_turns_current < num_turns_opponent:
        return 1
    elif num_turns_current > num_turns_opponent:
        return 0
    else:
        return 0.5

# import ranking metrics for rating calculations
from app.models import Boxer, RankingMetrics

# constants for use in the algorithms:

# elo c value
ELO_C = 10
# elo d value
ELO_D = 400
# default Glicko rating deviation if unavailable per fighter
GLICKO_RATING_DEVIATION = 50
# Trueskill beta value (standard deviation)
TRUESKILL_BETA = 100

"""
function to predict the fight winner with the elo algorithm:
fighter 1 win probability = 1/(1 + c^((fighter b rating - fighter a rating) / d)))
"""
def elo_winner(boxer_a, boxer_b):
    # calculate fighter rating values to inject into the algorithm. baseline rating of 1500
    # contribution of each fighter ranking metric to the overall rating is weighted based on importance
    a = RankingMetrics.query.get(boxer_a.id)
    b = RankingMetrics.query.get(boxer_b.id)

    # error prevention and defaults to fall back to in the event of null values for any metric in the database
    if not a:
        win_ratio_a = ko_ratio_a = 0.0
        wins_a = losses_a = 0
    else:
        win_ratio_a = a.win_ratio or 0.0
        ko_ratio_a = a.ko_ratio or 0.0
        wins_a = a.wins or 0
        losses_a = a.losses or 0

    if not b:
        win_ratio_b = ko_ratio_b = 0.0
        wins_b = losses_b = 0
    else:
        win_ratio_b = b.win_ratio or 0.0
        ko_ratio_b = b.ko_ratio or 0.0
        wins_b = b.wins or 0
        losses_b = b.losses or 0

    r_a = 1500 + (500 * win_ratio_a) + (250 * ko_ratio_a) + (5 * (wins_a - losses_a))
    r_b = 1500 + (500 * win_ratio_b) + (250 * ko_ratio_b) + (5 * (wins_b - losses_b))

    # calculation of fighter a and b win prob using the elo formula
    elo_prob_a = 1 / (1 + ELO_C ** ((r_b - r_a) / ELO_D))
    elo_prob_b = 1 - elo_prob_a

    # assign winner
    winner = boxer_a if elo_prob_a >= 0.5 else boxer_b
    winner_id = winner.id

    # string summarising the rating difference
    elo_differential = f"Elo rating disparity = {r_a - r_b:.2f}"

    # function return values for a boxer_a victory
    if winner is boxer_a:
        # calculation of fighter a KO and decision likelihood
        if (r_a - r_b) > 100:
            prob_ko = 0.7
            # a large gap in the rating values produces a higher KO likelihood,
            win_type = 'K.O.'
            elo_prob = elo_prob_a
            return winner_id, elo_prob, win_type, elo_differential, prob_ko

        # otherwise, for a small gap in the rating values, a ko is less likely and decision win is more likely
        else:
            prob_ko = 0.3
            win_type = 'Decision'
            elo_prob = elo_prob_a
            return winner_id, elo_prob, win_type, elo_differential, prob_ko

    # function return values for a boxer_b victory
    if winner is boxer_b:
        # calculation of fighter b KO and decision likelihood
        if (r_b - r_a) > 100:
            # a large gap in the rating values produces a higher KO likelihood,
            prob_ko = 0.7
            win_type = 'K.O.'
            elo_prob = elo_prob_b
            return winner_id, elo_prob, win_type, elo_differential, prob_ko

        # otherwise, for a small gap in the rating values, a ko is less likely and decision win is more likely
        else:
            prob_ko = 0.3
            win_type = 'Decision'
            elo_prob = elo_prob_b
            return winner_id, elo_prob, win_type, elo_differential, prob_ko
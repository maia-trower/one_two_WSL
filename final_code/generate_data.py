# script to run to generate necessary data for plots
import pandas as pd
from one_two.functions import get_pass_data, get_one_twos


def get_season_one_twos(comp, season, path, s, p, c):
    """
    get all one-two passes for all teams from specified season of competition
    see attached report for explanation of thresholds
    :param comp: int, competition id
    :param season: int, season id
    :param path: str, path to retrieve 360 data
    :param s: float, time threshold for defining one-two pass
    :param p: float, progression threshold for defining one-two pass
    :param c: float, carry threshold for defining one-two passes
    :return: dataframe, one-two passes for season
    """
    # this function should return a single data frame of all one-two passes for a whole season

    # get all passes per match
    all_matches_passes = get_pass_data(comp, season, None, path, all_teams=True)

    # then get only the one-two passes and store in dict
    one_two_dict = {}
    for key in all_matches_passes.keys():
        one_two_dict[key] = get_one_twos(all_matches_passes[key], sec_threshold=s, prog_threshold=p, carry_threshold=c)

    # then concatenate all matches into single df
    # (note - could do this directly but dict may be more useful for later stuff - review this !)
    one_twos_aggregated = pd.DataFrame([])
    for key in one_two_dict.keys():
        all_onetwos = pd.concat([one_twos_aggregated, one_two_dict[key]], axis=0)

    return all_onetwos


def get_player_counts():

import pandas as pd
import json
from one_two.functions import get_pass_data, get_one_twos, get_player_one_twos, plot_match_one_twos


def main(input_file):
    """
    main function for generating all one-two passes for specified team for a specified tournament
    also then filters by players listed in input file
    and then plots the successful one-two with 360 information to show positions of other players
    TODO - change hard-coded Beth Mead plots to plot any successful one-two (i.e. one that results in an assist)
    :param input_file: json, dictionary of inputs
    :return: None
    """
    # read in inputs
    with open(f"inputs/{input_file}.json", "r") as f:
        inputs = json.load(f)
    comp = inputs["competition_name"]
    comp_id = inputs["competition_id"]
    season_id = inputs["season_id"]
    path = inputs["path_to_360"]
    team = inputs["team"]
    players = inputs["players"]

    # get all passes for England for whole tournament
    pass_data = get_pass_data(competition_ID=comp_id, season_ID=season_id, team=team, data_path=path)

    # then get one_twos
    one_twos_eng_dict = {}
    for match in pass_data.keys():
        one_twos_eng_dict[match] = get_one_twos(match=pass_data[match])

    # get one-twos for specified players for all matches
    player_data = {}
    for player in players:
        player_data[player] = pd.DataFrame([])
        for key in one_twos_eng_dict.keys():
            player_temp = get_player_one_twos(player=player, data=one_twos_eng_dict[key])
            player_data[player] = pd.concat([player_data[player], player_temp])

    # get key beth mead one-two
    BM_data = player_data["Bethany Mead"]
    BM_assist = BM_data.iloc[2:4, :]

    plot_match_one_twos(data=BM_assist, save=True, grid=False)


if __name__ == '__main__':
    main(input_file="input_v2")
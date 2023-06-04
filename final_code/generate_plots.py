# generate all plots for presentation
from one_two.functions import get_player_one_twos, plot_one_two_heatmaps, get_season_one_twos, get_player_counts, \
    total_one_two_stack, key_pass_relplot
import json

# TODO save data generated here so I can rerun plots without re-generating data
# TODO once ^ is done then add a "if data exists" statement - if exists, load it, if not, generate it

def main(input_file):
    """
    main function for generating plots of interest - get all one-twos for competition + season
    then find which players are most involved and do a bar plot for that
    then assess the one-two value and plot by open/close/value - labelling specified players
    and for each player specified, show their open/close heatmap
    :param input_file: json, dictionary of inputs
    :return: None
    """
    # read in inputs
    with open(f"inputs/{input_file}.json", "r") as f:
        inputs = json.load(f)
    comp = inputs["competition_name"]
    comp_id = inputs["competition_id"]
    season_id = inputs["season_id"]
    players = inputs["players"]
    n = inputs["n"]
    s_thresh = inputs["threshold_seconds"]
    p_thresh = inputs["threshold_progression"]
    c_thresh = inputs["threshold_carry"]

    # get data here
    one_two_agg = get_season_one_twos(comp=comp_id, season=season_id, path="", s=s_thresh, p=p_thresh, c=c_thresh)
    one_two_player_counts = get_player_counts(one_two_agg)

    # then do the plots in order
    # 1. stacked bar plot
    total_one_two_stack(one_twos=one_two_player_counts, n=n)

    # print percentage of open and closed for BM and FK (for slides):
    BM_opened = 100*(one_two_player_counts[one_two_player_counts["player"]=="Bethany Mead"]["open_count"].iloc[0]/\
                one_two_player_counts[one_two_player_counts["player"]=="Bethany Mead"]["total_count"].iloc[0])
    print(f"percentage of one-twos involving Beth Mead that Mead opens: {BM_opened}")
    FK_opened = 100*(one_two_player_counts[one_two_player_counts["player"] == "Francesca Kirby"]["open_count"].iloc[0] / \
                one_two_player_counts[one_two_player_counts["player"] == "Francesca Kirby"]["total_count"].iloc[0])
    print(f"percentage of one-twos involving Fran Kirby that Kirby opens: {FK_opened}")

    # print key pass percentage for BM and FK (for slides):
    BM_pc = one_two_player_counts[one_two_player_counts["player"]=="Bethany Mead"]["key_pc"].iloc[0]
    FK_pc = one_two_player_counts[one_two_player_counts["player"]=="Francesca Kirby"]["key_pc"].iloc[0]
    print(f"percentage of one-twos involving Mead that are key passes: {BM_pc}")
    print(f"percentage of one-twos involving Kirby that are key passes: {FK_pc}")

    # 2. relplot
    key_pass_relplot(one_twos=one_two_player_counts, n=n, name_labels=players)

    # 3. heatmap plot
    # do heatmap for each player
    player_data = {}
    for player in players:
        player_data[player] = get_player_one_twos(player, one_two_agg)
        plot_one_two_heatmaps(data=player_data[player], competition=comp, season=season_id, team=player, combined=False)


if __name__ == '__main__':
    main(input_file="input_v1")


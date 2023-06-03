# generate all plots for presentation
from one_two.functions import get_player_one_twos, plot_one_two_heatmaps, get_season_one_twos, get_player_counts, \
    total_one_two_stack, key_pass_relplot
import json

# TODO set params fontsize etc

def main(input_file):
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


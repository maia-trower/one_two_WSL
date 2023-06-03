# generate all plots for presentation
from one_two.functions import get_player_one_twos, plot_one_two_heatmaps, get_season_one_twos, get_player_counts, \
    total_one_two_stack, key_pass_relplot

# TODO set params fontsize etc


if __name__ == '__main__':
    # read in inputs
    comp = inputs["competition_name"]
    comp_id = inputs["competition_id"]
    season_id = inputs["season_id"]
    players = inputs["players"]
    n = inputs["n"]

    # get data here
    one_two_agg = get_season_one_twos(comp=comp_id, season=season_id)
    open_player_counts, close_player_counts = get_player_counts()
    # combine open and close for stacked plot
    one_two_player_counts = open_player_counts.merge(close_player_counts, on="player", how="outer").rename(
        columns={"count_x": "open_count", "count_y": "close_count", "team_x": "team"})
    one_two_player_counts = one_two_player_counts.drop(columns=["team_y"])

    # then do the plots in order
    # 1. stacked bar plot
    total_one_two_stack(one_twos=one_two_player_counts, n=n)

    # 2. relplot
    key_pass_relplot(one_twos=one_two_player_counts, n=n, name_labels=players)

    # 3. heatmap plot
    # do heatmap for each player
    player_data={}
    for player in players:
        player_data[player] = get_player_one_twos(player, one_two_agg)
        plot_one_two_heatmaps(data=player_data[player], competition=comp, season=season_id)




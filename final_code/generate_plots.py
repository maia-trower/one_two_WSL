# generate all plots for presentation
import matplotlib.pyplot as plt
import seaborn as sns
from generate_data import get_season_one_twos, get_player_counts

# TODO set params fontsize etc


def total_one_two_stack(one_twos, n):
    """
    Generate stacked bar plot showing top n players ranked by number of 1-2 passes

    :param one_twos: dataframe, with columns player, open_count, close_count, team, total_count, key_pc
    :param counts:
    :param n:
    :return:
    """
    # use surnames only
    surnames = []
    for player in one_twos.player:
        surnames.append(player.split(" ")[-1])

    one_twos["surname"] = surnames

    fig, ax = plt.subplots(figsize=(12, 8))
    # plt.title("Players With Most One-Two Passes Per Team (WSL 20/21)")

    # make color dict
    unique = one_twos["team"].unique()
    palette = dict(zip(unique, sns.color_palette(n_colors=len(unique))))
    one_twos.sort_values(by="total_count", ascending=False).head(n).set_index("surname")[
        ["open_count", "close_count"]].plot(kind="bar", stacked=True, color=["red", "green"], ax=ax)
    plt.savefig(f"slide_plots/open_close_stack_top{n}.png")
    plt.xticks(rotation=0)
    plt.ylabel("Count")
    plt.xlabel("Player")
    plt.show()


def key_pass_relplot(one_twos, n, name_labels=[]):
    """
    Generate seaborn relplot showing how many 1-2s a player opened vs closed, with
    size corresponding to percentage of 1-2s that are key passes (see attached report)
    :param one_twos: dataframe, with columns player, open_count, close_count, team, total_count, key_pc
    :param n: how many point to plot
    :param name_labels: which names to annotate on plot (surname only)
    :return:
    """
    # plot opening against closing, scatter plot size = key pass percentage
    sns.set(rc={"figure.figsize": (20, 15)})

    p = sns.relplot(x="open_count", y="close_count", data=one_twos.head(n), hue="team", size="key_pc", sizes=(10, 500))
    ax = p.axes[0, 0]
    ax.set_xlabel("Opened")
    ax.set_ylabel("Closed")

    for idx, row in one_twos.head(n).iterrows():
        x = row[1]
        y = row[3]
        name = row[0]
        if name in [name_labels]:
            ax.text(x - 0.25, y + 0.5, name.split(" ")[-1], horizontalalignment='right')
    plt.savefig(f"slide_plots/open_closed_key_relplot_top{n}.png")
    plt.show()


def open_close_heatmaps():

if __name__ == '__main__':
    # read in inputs
    comp = inputs["competition_name"]
    comp_id = inputs["competition_id"]
    season_id = inputs["season_id"]
    players = inputs["players"]
    n = inputs["n"]

    # get data here
    one_two_agg = get_season_one_twos(comp=comp_id, season=season_id)
    one_two_player_counts = get_player_counts()
    # then do the plots in order

    # stacked bar plot
    total_one_two_stack(one_twos=one_two_player_counts, n=n)

    # relplot
    key_pass_relplot(one_twos=one_two_player_counts, n=n, name_labels=players)

    # heatmap plot
    # do heatmap for each player
    player_data={}
    for player in players:
        player_data[player] = get_player_one_twos(player, one_two_agg)
        plot_one_two_heatmaps(data=player_data[player], competition=comp, season=season_id)




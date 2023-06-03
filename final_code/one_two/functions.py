import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch
from statsbombpy import sb
import numpy as np


# data functions
def get_player_one_twos(player, data):
    idx = []
    for i in range(len(data)):
        player1 = data["player"].iloc[i]
        player2 = data["pass_recipient"].iloc[i]

        if player1 == player or player2 == player:
            idx.append(i)

    data = data.iloc[idx, :]

    return data


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

def get_player_counts(data_agg):
    # split into opening and closing passes
    open_agg = data_agg.iloc[::2, :]
    close_agg = data_agg.iloc[1::2, :]

    # then count number of one-twos for each player
    open_counts = open_agg.player.value_counts()
    open_counts = open_counts.reset_index()
    close_counts = close_agg.player.value_counts()
    close_counts = close_counts.reset_index()

    # add team info
    open_counts = get_team_info(open_counts, open_agg)
    close_counts = get_team_info(close_counts, close_agg)

    return open_counts, close_counts


def get_pass_data(competition_ID, season_ID, team, data_path, all_teams=False):
    """
    get all pass info (event data plus 360 data) for specified competition and season, for specified HOME team only
    :param competition_ID: int, id number of competition
    :param season_ID: int, id number of season
    :param team: str, required team name
    :param data_path: str, path to 360 data
    :return: dict, dictionary of pd dataframes with all pass data for team from season and competition
    """

    # load all matches from specified competition and season
    matches_df = sb.matches(competition_id=competition_ID, season_id=season_ID)

    # get id number of all matches played by specified team (home & away)
    if competition_ID==53:
        team = f"{team} Women's"

    if all_teams:
        match_ids = matches_df["match_id"]
    else:
        match_ids = np.concatenate([np.array(matches_df[matches_df["home_team"] == team]["match_id"]),
                                    np.array(matches_df[matches_df["away_team"] == team]["match_id"])])

    # loop through all matches
    all_passes = {}
    for matchid in match_ids:
        # get event data ...
        events = sb.events(match_id=matchid)
        # ... and get 360 data if it exists ...
        if competition_ID==53:
            threesixty = pd.read_json(f"{data_path}/{matchid}.json")

            # ... merge into single dataframe
            df = pd.merge(left=events, right=threesixty, left_on='id', right_on='event_uuid', how='left')
        else:
            df = events

        # now filter for passes (completed passes only) ...
        passes_df = df.dropna(subset=["pass_recipient"])
        passes_df = passes_df[passes_df["pass_outcome"].isna()]

        if not all_teams:
            # ... remove opposition's passes
            passes_df = passes_df[passes_df["team"]==team]

        # store each dataframe of passing data in a dict (key=match id)
        all_passes[str(matchid)] = passes_df
    return all_passes


def get_one_twos(match, sec_threshold=5, prog_threshold=0.75, carry_threshold=5):
    """
    returns one-two data from passing data
    :param match: dataframe, event and 360 data of passes
    :param sec:
    :param prog_threshold:
    :param carry_threshold:
    :return:
    """

    # convert timestamp into seconds
    match["time_in_secs"] = match["minute"]*60 + match["second"]

    # empty list to store index of one-two passes
    one_two_idx = []

    # loop through each pass ...
    for i in range(len(match)):
        player1 = match["player"].iloc[i]
        player2 = match["pass_recipient"].iloc[i]

        # check passes in next n seconds only
        pass_time_sec = match["time_in_secs"].iloc[i]
        cutoff = pass_time_sec + sec_threshold
        next_passes_df = match[match["time_in_secs"].between(pass_time_sec, cutoff, inclusive="both")]

        # for every pass that happens in the next n seconds ...
        for j in range(len(next_passes_df)):
            # ... select those where player 2 passes back to player 1 ...
            if next_passes_df["player"].iloc[j] == player2 and next_passes_df["pass_recipient"].iloc[j] == player1:
                # ... then calculate change in distance to goal line to see if the pass combo progresses up the pitch
                line_dist_start = 120 - match["location"].iloc[i][0]
                line_dist_end = 120 - next_passes_df["pass_end_location"].iloc[j][0]

                # ... or if it progresses towards the centre of the goal
                start_goal_dist = np.sqrt(np.power(match["location"].iloc[i][0] - 120, 2) +
                                          np.power(match["location"].iloc[i][1] - 40, 2))
                end_goal_dist = np.sqrt(np.power(next_passes_df["pass_end_location"].iloc[j][0] - 120, 2) +
                                        np.power(next_passes_df["pass_end_location"].iloc[j][1] - 40, 2))

                # ... and calculate distance between end of pass 1 and start of pass 2 to see if player 2 is moving
                pass_dist = np.sqrt(np.power(match["pass_end_location"].iloc[i][0]-
                                             next_passes_df["location"].iloc[j][0],2) +
                                    np.power(match["pass_end_location"].iloc[i][1]-
                                             next_passes_df["location"].iloc[j][1],2))

                # store only the passes that satisfy the specified conditions
                if line_dist_end < line_dist_start*prog_threshold and pass_dist < carry_threshold:
                    one_two_idx.append([match.index[i], next_passes_df.index[j]])
                elif end_goal_dist < start_goal_dist*prog_threshold and pass_dist < carry_threshold:
                    one_two_idx.append([match.index[i], next_passes_df.index[j]])


    # select the one-twos from the original pass dataframe
    all_onetwos = match.loc[np.array(one_two_idx).reshape(1,-1)[0]]

    if len(one_two_idx) == 0:
        return pd.DataFrame([])
    else:

        # make extra location columns for easier plotting !
        all_onetwos[["x_start", "y_start"]] = pd.DataFrame(all_onetwos.location.tolist(), index=all_onetwos.index)
        all_onetwos[["x_end", "y_end"]] = pd.DataFrame(all_onetwos.pass_end_location.tolist(), index=all_onetwos.index)

        return all_onetwos


def get_team_info(count_data, agg_data):
    teams = []
    for i in range(len(count_data)):
        player = count_data["player"].iloc[i]
        team = agg_data[agg_data["player"] == player]["possession_team"].iloc[0]
        teams.append(team)

    count_data["team"] = teams

    return count_data



# plotting functions
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

    # # make color dict - only for coloring by team
    # unique = one_twos["team"].unique()
    # palette = dict(zip(unique, sns.color_palette(n_colors=len(unique))))
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


def plot_one_two_heatmaps(data, competition, season, team, combined=True):
    # split into opening and closing passes

    open_12 = data.loc[data.index[::2]]
    close_12 = data.loc[data.index[1::2]]

    p = Pitch(line_color="white", pitch_color="green", pitch_type="statsbomb")

    fig, axs = p.grid(ncols=2, nrows=1,grid_height=0.9, title_height=0.06, axis=False, endnote_height=0, title_space=0, endnote_space=0)
    plt.figure(figsize=(12, 8))
    for i, ax in zip(np.arange(2), axs['pitch'].flat):
        if i==0:
            df = open_12
            ax.set_title("One-Two Opening Shot")
            kdeplot = p.kdeplot(
            x=df.x_start,
            y=df.y_start,
            fill=True,
            shade_lowest=False,
            alpha=.5,
            n_levels=10,
            cmap='viridis',
            cbar=True,
            cbar_kws={"shrink": 0.5},
            ax=ax
        )
        else:
            df = close_12
            ax.set_title("One-Two Closing Shot")
            kdeplot = p.kdeplot(
                x=df.x_end,
                y=df.y_end,
                fill=True,
                shade_lowest=False,
                alpha=.5,
                n_levels=10,
                cmap='viridis',
                cbar=True,
                cbar_kws={"shrink": 0.5},
                ax=ax
            )



    if combined:
        plt.savefig(f"{competition}_{season}_heatmap.png")
    else:
        plt.savefig(f"{competition}_{season}_{team}_heatmap.png")
    plt.show()
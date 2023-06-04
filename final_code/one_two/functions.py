import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch
from statsbombpy import sb
import numpy as np

# TODO set plot parameters up here to make it the same across all plots

# data functions
def get_player_one_twos(player, data):
    """
    Given a dataframe of one-two passes, filter it to return only one-twos involving specified player
    :param player: str, the name of the player to filter by
    :param data: dataframe, a df of one-two passes (for match, season, team, etc ...)
    :return: dataframe, the original dataframe filtered for player
    """

    # intialise list to store indices
    idx = []

    # loop through all one-twos
    for i in range(len(data)):
        player1 = data["player"].iloc[i]
        player2 = data["pass_recipient"].iloc[i]

        if player1 == player or player2 == player:
            idx.append(i)

    # filter by selected indices
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

    # get all passes per match
    all_matches_passes = get_pass_data(comp, season, None, path, all_teams=True)

    # then get only the one-two passes and store in single dataframe
    one_two_agg = pd.DataFrame([])
    for key in all_matches_passes.keys():
        match_one_twos = get_one_twos(all_matches_passes[key], sec_threshold=s, prog_threshold=p, carry_threshold=c)
        one_two_agg = pd.concat([one_two_agg, match_one_twos], axis=0)

    return one_two_agg


def key_one_two_percentage(data):
    """
    calculate how many one-twos lead to a shot or goal as a percentage
    TODO tidy up the try/except loop (check existence of col instead ?)
    :param data: dataframe, one-twos
    :return:
    """
    try:
        shot_assists = data.pass_shot_assist.value_counts().iloc[0]
    except Exception:
        shot_assists = 0
    try:
        goal_assists = data.pass_goal_assist.value_counts().iloc[0]
    except Exception:
        goal_assists = 0

    key_pass_pc = 100*(shot_assists + goal_assists)/(0.5*len(data))

    return key_pass_pc


def get_player_counts(data_agg):
    """
    given all one-twos for season/comp, return a dataframe of stats for each player involved in one-twos
    :param data_agg: dataframe, contains one-two passes (e.g. per season, per comptetition etc ...)
    :return: dataframe, df of stats per player with number of one-twos total, number opened/closed, and key percentage
    """
    # split into opening and closing passes
    # TODO could go straight to merged dataframe here (don't need separate ones anymore)
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

    # combine open and close for stacked plot
    one_two_counts = open_counts.merge(close_counts, on="player", how="outer").rename(
        columns={"count_x": "open_count", "count_y": "close_count", "team_x": "team"})
    one_two_counts = one_two_counts.drop(columns=["team_y"])
    # add a total count col
    one_two_counts["total_count"] = one_two_counts["open_count"] + one_two_counts["close_count"]

    # then find key pass percentage ...
    player_data = {}
    pcs = []
    for player in one_two_counts["player"]:
        player_data[player] = get_player_one_twos(player, data_agg)
        pc = key_one_two_percentage(player_data[player])
        pcs.append(pc)

    one_two_counts["key_pc"] = pcs
    return one_two_counts


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

    # TODO check how to store apostrophes in json string so I can get rid of this bit
    if competition_ID==53:
        team = f"{team} Women's"

    # get id number of all matches played by specified team (home & away) or by everyone if all_teams is true
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
    see attached report for info on thresholds
    :param match: dataframe, event and 360 data of passes
    :param sec_threshold: float, time threshold for defining one-two pass
    :param prog_threshold: float, progression threshold for defining one-two pass
    :param carry_threshold: float, carry threshold for defining one-two passes
    :return: dataframe, all one-twos found in passing data
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
        # return empty frame and notify if none found
        print("No one-twos found.")
        return pd.DataFrame([])
    else:
        # make extra location columns for easier plotting
        all_onetwos[["x_start", "y_start"]] = pd.DataFrame(all_onetwos.location.tolist(), index=all_onetwos.index)
        all_onetwos[["x_end", "y_end"]] = pd.DataFrame(all_onetwos.pass_end_location.tolist(), index=all_onetwos.index)

        return all_onetwos


def get_team_info(count_data, agg_data):
    """
    given count dataframe find the team for each player
    :param count_data: dataframe, df of one-two stats for players
    :param agg_data: dataframe, df of all the one-two passes from which count_data was computed
    :return:
    """
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
    TODO find a way to add team info that doesn't make it too crowded (maybe colour by team and then shade darker/lighter for open/close ??)
    :param one_twos: dataframe, with columns player, open_count, close_count, team, total_count, key_pc
    :param counts: dataframe, datafromae of one-two stats per player
    :param n: int, number of players to plot
    :return:
    """
    # use surnames only
    surnames = []
    for player in one_twos.player:
        surnames.append(player.split(" ")[-1])

    one_twos["surname"] = surnames

    fig, ax = plt.subplots(figsize=(12, 8))

    # # make color dict - only for coloring by team
    # unique = one_twos["team"].unique()
    # palette = dict(zip(unique, sns.color_palette(n_colors=len(unique))))

    one_twos.sort_values(by="total_count", ascending=False).head(n).set_index("surname")[
        ["open_count", "close_count"]].plot(kind="bar", stacked=True, color=["red", "green"], ax=ax)
    plt.xticks(rotation=0)
    ax.set_ylabel("Count")
    ax.set_xlabel("Player")
    plt.savefig(f"slide_plots/open_close_stack_top{n}.png")
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

    p = sns.relplot(x="open_count", y="close_count", data=one_twos.head(2*n), hue="team", size="key_pc", sizes=(10, 500))
    ax = p.axes[0, 0]
    ax.set_xlabel("Opened")
    ax.set_ylabel("Closed")

    for idx, row in one_twos.head(n).iterrows():
        x = row[1]
        y = row[3]
        name = row["player"]
        if name in name_labels:
            ax.text(x - 0.25, y + 0.5, name.split(" ")[-1], horizontalalignment='right')

    plt.savefig(f"slide_plots/open_closed_key_relplot_top{2*n}.png")
    plt.show()


def plot_match_one_twos(data, save_path="", save=True, grid=False):
    """
    generate plot to display one-two passes on a pitch with 360 info to show other players if 360 freeze frame exists
    :param data: dataframe, one-two passes
    :param save_path: str, where to save the plot if not the default path
    :param save: bool, whether to save it
    :param grid: bool, True if you want to return a grid of all one-two passes in data, False if you only have one to display
    :return:
    """
    if grid:
        one_twos = np.array(data.index).reshape(-1, 2)
        df = one_twos.reshape(-1, 2)

        # number of rows:
        n_rows = int(np.ceil(len(df)/2))
        n_cols = 2

        p = Pitch(line_color="white", pitch_color="green", pitch_type="statsbomb")

        fig, axs = p.grid(ncols=n_cols, nrows=n_rows, grid_height=0.85, title_height=0.06, axis=False, endnote_height=0,
                          title_space=0, endnote_space=0)

        plt.figure(figsize=(12, 8))

        # for each one-two ...
        for row, ax in zip(df, axs['pitch'].flat):
            onetwodf = data.loc[row]

            i = 0
            p.arrows(xstart=onetwodf["x_start"].iloc[i], ystart=onetwodf["y_start"].iloc[i], xend=onetwodf["x_end"].iloc[i],
                     yend=onetwodf["y_end"].iloc[i], ax=ax, width=2, headwidth=5, headlength=5, color="blue")
            p.arrows(xstart=onetwodf["x_start"].iloc[i + 1], ystart=onetwodf["y_start"].iloc[i + 1],
                     xend=onetwodf["x_end"].iloc[i + 1], yend=onetwodf["y_end"].iloc[i + 1], ax=ax, width=2, headwidth=5,
                     headlength=5, color="red")

            try:
                # plot other players in the frame - note that the players' locations are at the *close* of the one-two
                for x in onetwodf.iloc[i + 1]["freeze_frame"]:
                    if x["teammate"]:
                        color = "white"
                        p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=1, marker='x')
                    else:
                        color = "white"
                        p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=1)
            except Exception:
                pass

    else:
        p = Pitch(line_color="white", pitch_color="green", pitch_type="statsbomb")
        fig, ax = p.draw(figsize=(12, 8))

        for i in range(len(data)):

            if i % 2:
                color = "blue"
            else:
                color = "blue"

            p.arrows(xstart=data["x_start"].iloc[i], ystart=data["y_start"].iloc[i],
                     xend=data["x_end"].iloc[i], yend=data["y_end"].iloc[i], ax=ax, width=2,
                     headwidth=5, headlength=5, color=color)
        try:
            # plot other players in the frame - note that the players' locations are at the *close* of the one-two
            for x in data.iloc[1]["freeze_frame"]:
                if x["teammate"]:
                    color = "blue"
                    p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=1, marker='x')
                else:
                    color = "red"
                    p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=1)
        except Exception:
            pass

        if save:
            plt.savefig(f"slide_plots/{save_path}match_one_two_360.png")
            plt.show()



def plot_one_two_heatmaps(data, competition, season, team, combined=True):
    """
    plot heatmap for location of opening and closing passes on a 1x2 grid
    :param data: dataframe, one-two passes to plot
    :param competition: int/str, some identifier (i.e. name or id) for the competition (used for save path)
    :param season: int/str, some identifier for the season
    :param team: str, team name (could also be used for player name)
    :param combined: bool, indicates if the data is aggregated over all teams/players
    :return:
    """

    # split into opening and closing passes
    open_12 = data.loc[data.index[::2]]
    close_12 = data.loc[data.index[1::2]]

    p = Pitch(line_color="white", pitch_color="green", pitch_type="statsbomb")
    p = Pitch(line_color="black", pitch_color="white", pitch_type="statsbomb")

    fig, axs = p.grid(ncols=2, nrows=1,grid_height=0.9, title_height=0.06, axis=False, endnote_height=0, title_space=0, endnote_space=0)
    # plt.figure(figsize=(12, 8))
    for i, ax in zip(np.arange(2), axs['pitch'].flat):
        if i==0:
            df = open_12
            ax.set_title("Opening Pass", fontsize=30)
            p.kdeplot(
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
            ax.set_title("Closing Pass", fontsize=30)
            p.kdeplot(
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
        plt.savefig(f"slide_plots/{competition}_{season}_heatmap.png")
    else:
        plt.savefig(f"slide_plots/{competition}_{season}_{team}_heatmap.png")

    plt.show()
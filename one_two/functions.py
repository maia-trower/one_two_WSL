import pandas as pd
from statsbombpy import sb
from mplsoccer import Pitch
import numpy as np
import matplotlib.pyplot as plt


def get_pass_data(competition_ID, season_ID, team, data_path):
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
    match_ids = np.concatenate([np.array(matches_df[matches_df["home_team"]==team]["match_id"]), np.array(matches_df[matches_df["away_team"]==team]["match_id"])])

    # loop through all matches for the team
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

        # ... and remove opposition's passes
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

    # make extra location columns for easier plotting
    all_onetwos[["x_start", "y_start"]] = pd.DataFrame(all_onetwos.location.tolist(), index=all_onetwos.index)
    all_onetwos[["x_end", "y_end"]] = pd.DataFrame(all_onetwos.pass_end_location.tolist(), index=all_onetwos.index)

    return all_onetwos


def plot_match_one_twos(data, save_path="", save=True, grid=False):
    if grid:
        one_twos = np.array(data.index).reshape(-1, 2)
        df = one_twos.reshape(-1, 2)

        # number of rows:
        n_rows = len(df)
        n_cols = 2

        p = Pitch(line_color="black", pitch_color="green", pitch_type="statsbomb")

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
                for x in onetwodf.iloc[i + 1]["freeze_frame"]:
                    if x["teammate"]:
                        color = "white"
                        p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=0.3, marker='x')
                    else:
                        color = "white"
                        p.scatter(x=x["location"][0], y=x["location"][1], ax=ax, c=color, s=100, alpha=0.3)
            except Exception:
                pass

    else:
        p = Pitch(line_color="black", pitch_color="green", pitch_type="statsbomb")
        fig, ax = p.draw(figsize=(12, 8))

        for i in range(len(data)):

            if i % 2:
                color = "blue"
            else:
                color = "red"

            p.arrows(xstart=data["x_start"].iloc[i], ystart=data["y_start"].iloc[i],
                     xend=data["x_end"].iloc[i], yend=data["y_end"].iloc[i], ax=ax, width=2,
                     headwidth=5, headlength=5, color=color)


        if save:
            plt.savefig(save_path)
            plt.show()


def plot_one_two_heatmaps(data, competition, season, team, combined=True):
    # split into opening and closing passes

    open_12 = data.loc[data.index[::2]]
    close_12 = data.loc[data.index[1::2]]

    p = Pitch(line_color="white", pitch_color="green", pitch_type="statsbomb")

    fig, ax = p.grid(grid_height=0.9, title_height=0.06, axis=False, endnote_height=0, title_space=0, endnote_space=0)

    kdeplot = p.kdeplot(
        x=open_12.x_start,
        y=open_12.y_start,
        fill=True,
        shade_lowest=False,
        alpha=.5,
        n_levels=10,
        cmap='viridis',
        cbar=True,
        cbar_kws={"shrink": 0.5},
        ax=ax['pitch']
    )

    if combined:
        plt.savefig(f"{competition}_{season}_heatmap_open.png")
    else:
        plt.savefig(f"{competition}_{season}_{team}_heatmap_open.png")
    plt.show()

    fig, ax = p.grid(grid_height=0.9, title_height=0.06, axis=False, endnote_height=0, title_space=0, endnote_space=0)

    kdeplot = p.kdeplot(
        x=close_12.x_end,
        y=close_12.y_end,
        fill=True,
        shade_lowest=False,
        alpha=.5,
        n_levels=10,
        cmap='viridis',
        cbar=True,
        cbar_kws={"shrink": 0.5},
        ax=ax['pitch']
    )

    if combined:
        plt.savefig(f"{competition}_{season}_heatmap_close.png")
    else:
        plt.savefig(f"{competition}_{season}_{team}_heatmap_close.png")
    plt.show()


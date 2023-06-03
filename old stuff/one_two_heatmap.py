import pickle
import json

import matplotlib.pyplot as plt

from one_two.functions import get_one_twos
import pandas as pd
from mplsoccer import Pitch


def main(input_file):
    # load in dictionary of inputs here
    with open(f"inputs/{input_file}.json", "r") as f:
        inputs = json.load(f)

    comp = inputs["competition_id"]
    season = inputs["season_id"]
    team = inputs["team_name"]
    path = inputs["path_to_360"]
    sec_thresh = inputs["threshold_seconds"]
    p_thresh = inputs["threshold_progression"]
    c_thresh = inputs["threshold_carry"]
    figpath = inputs["fig_path"]
    save_data = inputs["data_save_path"]

    with open(f"data/{comp}_{season}_{team}.pickle", "rb") as f:
        data_dict = pickle.load(f)

    combined = pd.DataFrame()

    for key in data_dict.keys():
        one_twos = get_one_twos(match=data_dict[key], sec_threshold=sec_thresh, prog_threshold=p_thresh,
                                carry_threshold=c_thresh)
        combined = pd.concat([combined, one_twos], axis=0)

    # split into opening and closing passes

    open_12 = combined.loc[combined.index[::2]]
    close_12 = combined.loc[combined.index[1::2]]

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

    plt.savefig(f"{comp}_{season}_{team}_heatmap_open.png")
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

    plt.savefig(f"{comp}_{season}_{team}_heatmap_close.png")
    plt.show()


if __name__ == '__main__':
    main("arsenal_WSL_19")
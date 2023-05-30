from one_two.functions import get_pass_data, get_one_twos, plot_match_one_twos
import pickle
import json


def main(country):
    # load in dictionary of inputs here
    with open(f"inputs/{country}_euros.json", "r") as f:
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

    all_matches = get_pass_data(competition_ID=comp, season_ID=season, team=team, data_path=path)

    # save dictionary as pickle file
    with open(f"{save_data}{comp}_{season}_{team}.pickle", "wb") as f:
        pickle.dump(all_matches, f, protocol=pickle.HIGHEST_PROTOCOL)

    for key in all_matches.keys():
        print(key)
        one_twos = get_one_twos(match=all_matches[key], sec_threshold=sec_thresh, prog_threshold=p_thresh, carry_threshold=c_thresh)

        plot_path = figpath + f"{comp}_{season}_{team}_{key}.png"
        plot_match_one_twos(data=one_twos, title="", save_path=plot_path, save=True, grid=False)


if __name__ == '__main__':
    main("germany")

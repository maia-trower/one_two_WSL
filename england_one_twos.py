from one_two.functions import get_pass_data, get_one_twos, plot_match_one_twos


def main():
    # load in dictionary of inputs here
    # hard code temporarily
    inputs = {"competition_id": 53, "season_id": 106, "team_name": "England Women\'s",
              "path_to_360": "/home/s2113337/Documents/GitHub/open-data/data/three-sixty", "threshold_seconds": 5,
              "threshold_progression": 0.75, "threshold_carry": 5, "fig_path": "plots/"}

    comp = inputs["competition_id"]
    season = inputs["season_id"]
    team = inputs["team_name"]
    path = inputs["path_to_360"]
    sec_thresh = inputs["threshold_seconds"]
    p_thresh = inputs["threshold_progression"]
    c_thresh = inputs["threshold_carry"]
    figpath = inputs["fig_path"]

    all_matches = get_pass_data(competition_ID=comp, season_ID=season, team=team, data_path=path)

    for key in all_matches.keys():
        one_twos = get_one_twos(match=all_matches[key], sec_threshold=sec_thresh, prog_threshold=p_thresh, carry_threshold=c_thresh)

        plot_path = figpath + f"{comp}_{season}_{team}_{key}.png"
        plot_match_one_twos(data=one_twos, title="", save_path=plot_path, save=True, grid=False)


if __name__ == '__main__':
    main()

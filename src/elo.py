import math

import data


def set_fcs(teams, games):
    for g_index, game in games.iterrows():
        if game.home_id not in teams.index:
            games.at[g_index, "home_id"] = 9999
            games.at[g_index, "school"] = "FCS"
        if game.away_id not in teams.index:
            games.at[g_index, "away_id"] = 9999
            games.at[g_index, "school"] = "FCS"

    return teams


def process_week_games(teams, week_games, margin_of_victory=False):
    for g_index, game in week_games.iterrows():
        # home team win
        if game.home_points > game.away_points:
            # set wins and losses
            teams.at[game.home_id, "Wins"] += 1
            teams.at[game.away_id, "Losses"] += 1

            winner = "home"
            if margin_of_victory:
                mov = game.home_points - game.away_points
            else:
                mov = 0

        # away team win
        else:
            # set wins and losses
            teams.at[game.home_id, "Losses"] += 1
            teams.at[game.away_id, "Wins"] += 1

            winner = "away"
            if margin_of_victory:
                mov = game.away_points - game.home_points
            else:
                mov = 0

        teams = update_elo(
            teams,
            game.home_id,
            game.away_id,
            margin_of_victory=mov,
            winner=winner,
        )

    return teams


def update_elo(teams, home, away, margin_of_victory=0, winner=None):
    K = 50

    home_elo = teams.at[home, "Elo"]
    away_elo = teams.at[away, "Elo"]

    if winner == "home":
        outcome_h = 1
        outcome_a = 0
        winner_elo_diff = home_elo - away_elo
    elif winner == "away":
        outcome_h = 0
        outcome_a = 1
        winner_elo_diff = away_elo - home_elo
    else:
        raise Exception("'winner' param must be either 'home' or 'away'")

    expected_h = 1 / (1 + (10 ** ((away_elo - home_elo) / 400)))
    expected_a = 1 / (1 + (10 ** ((home_elo - away_elo) / 400)))

    if margin_of_victory > 0:
        mov_multiplier = math.log(margin_of_victory + 1) * (
            2.2 / (winner_elo_diff * 0.001 + 2.2)
        )

        new_elo_h = round(home_elo + (K * mov_multiplier * (outcome_h - expected_h)))
        new_elo_a = round(away_elo + (K * mov_multiplier * (outcome_a - expected_a)))
    else:
        new_elo_h = round(home_elo + (K * (outcome_h - expected_h)))
        new_elo_a = round(away_elo + (K * (outcome_a - expected_a)))

    teams.at[home, "Elo"] = new_elo_h
    teams.at[away, "Elo"] = new_elo_a

    return teams


def weight_by_conference(teams_df):
    df = teams_df.copy()

    df.loc[df["Conference"] == "ACC", "Elo"] = 1510
    df.loc[df["Conference"] == "American Athletic", "Elo"] = 1475
    df.loc[df["Conference"] == "Big 10", "Elo"] = 1540
    df.loc[df["Conference"] == "Big 12", "Elo"] = 1535
    df.loc[df["Conference"] == "Conference USA", "Elo"] = 1460
    df.loc[df["Conference"] == "FBS Independents", "Elo"] = 1500
    df.loc[df["Conference"] == "Mid American", "Elo"] = 1450
    df.loc[df["Conference"] == "Mountain West", "Elo"] = 1460
    df.loc[df["Conference"] == "Pac 12", "Elo"] = 1510
    df.loc[df["Conference"] == "SEC", "Elo"] = 1550
    df.loc[df["Conference"] == "Sun Belt", "Elo"] = 1480

    return df


def weight_by_recruiting(teams_df):
    df = teams_df.copy()

    recruit_df = data.load_recruiting()

    # get average recruit points
    avg_recruit = recruit_df["points"].mean()

    for idx, team in recruit_df.iterrows():
        recruit_score = team["points"]
        diff = recruit_score - avg_recruit

        df.loc[df["School"] == team.name, "Elo"] = diff / 2 + 1500

    return df


def get_elo_rankings(
    season="all", conference=False, recruiting=False, margin_of_victory=False
):
    teams_df = data.load_teams()

    if season == "all":
        season_list = range(2010, 2021)
    else:
        season_list = [int(season)]

    if conference:
        teams_df = weight_by_conference(teams_df)

    if recruiting:
        teams_df = weight_by_recruiting(teams_df)

    elo_col = teams_df["Elo"].copy()

    for season in season_list:
        games_df = data.load_games(season=season)
        elo_rankings_df = set_fcs(teams_df, games_df)

        # reset wins/losses
        elo_rankings_df["Wins"] = 0
        elo_rankings_df["Losses"] = 0

        elo_rankings_df["Elo"] = elo_col

        for i in range(16):
            elo_rankings_df = process_week_games(
                elo_rankings_df, games_df[games_df.week == i + 1], margin_of_victory
            )

        # revert elo towards the mean
        # this is so past results aren't weighted as heavily as results from the current season
        # it also simulates player turnover, coach turnover, etc. between seasons
        elo_col = revert_to_mean(elo_rankings_df["Elo"].copy())

    return elo_rankings_df


def revert_to_mean(s):
    mean = s.mean()

    for idx, val in s.iteritems():
        if val > mean:
            s[idx] -= 0.7 * (val - mean)
        else:
            s[idx] += 0.7 * (mean - val)

    return s

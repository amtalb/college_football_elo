import math
from datetime import datetime

from pandas import DataFrame, Series

import data


def set_fcs(teams: DataFrame, games: DataFrame) -> DataFrame:
    """
    Replace all FCS opponents with a placeholder value in the teams df

    Parameters:
        teams: DataFrame
            a df of all teams
        games: DataFrame
            a df of all games
    Returns:
        the teams df updated so all FCS opponents are replaced by the FCS placeholder
    """
    for g_index, game in games.iterrows():
        if game.home_id not in teams.index:
            games.loc[games["id"] == game.id, "home_id"] = 9999
            games.loc[games["id"] == game.id, "home_team"] = "FCS"
        if game.away_id not in teams.index:
            games.loc[games["id"] == game.id, "away_id"] = 9999
            games.loc[games["id"] == game.id, "away_team"] = "FCS"

    return teams


def process_week_games(
    teams: DataFrame, week_games: DataFrame, margin_of_victory: bool = False
) -> DataFrame:
    """
    Process all the games in a week and update elo accordingly

    Parameters:
        teams: DataFrame
            a df containing all teams
        week_games: DataFrame
            a df containing all games played in the week
        margin_of_victory: bool = False
            optionally weight elo by margin of victory
    Returns:
        a df of all teams with elo updated according to the week's games
    """
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


def update_elo(
    teams: DataFrame,
    home: str,
    away: str,
    margin_of_victory: int = 0,
    winner: str = None,
) -> DataFrame:
    """
    Process a game and update elo according to the results

    Parameters:
        teams: DataFrame
            a DataFrame of all teams
        home: str
            the home team
        away: str
            the away team
        margin_of_victory: int = 0
            how much the winning team won by
        winner: str = None
            The winning team name
    Returns:
        A DataFrame with elos updated according to game results

    """
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


def weight_by_conference(teams_df: DataFrame) -> DataFrame:
    """
    Weights the DataFrame elo by conference ranks

    Parameters:
        teams_df: DataFrame
            The DataFrame to weight

    Returns:
        The weighted DataFrame
    """
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


def weight_by_recruiting(teams_df: DataFrame) -> DataFrame:
    """
    Weights the DataFrame elo by recruiting ranks

    Parameters:
        teams_df: DataFrame
            The DataFrame to weight

    Returns:
        The weighted DataFrame
    """
    df = teams_df.copy()

    recruit_df = data.load_recruiting()

    # get average recruit points
    avg_recruit = recruit_df["points"].mean()

    for idx, team in recruit_df.iterrows():
        recruit_score = team["points"]
        diff = recruit_score - avg_recruit

        df.loc[df["School"] == team.name, "Elo"] = diff / 2 + 1500

    return df


def build_teams_df(season: str, conference: bool, recruiting: bool) -> DataFrame:
    """
    Build a DataFrame of all teams

    Parameters:
        season: str
            The season to generate teams from
        conference: bool
            Optionally weight elo by conference strength
        recruiting: bool
            Optionally weight elo by recruiting strength

    Returns:
        A DataFrame containing all teams
    """
    if season == "all":
        teams_df = data.load_teams()
    else:
        teams_df = data.load_teams(season)

    if conference:
        teams_df = weight_by_conference(teams_df)

    if recruiting:
        teams_df = weight_by_recruiting(teams_df)

    return teams_df


def build_season_list(season: str) -> list[int]:
    """
    Generates a list of seasons

    Parameters:
        season: str
            Can either be "all" which will return a list of the 10 previous seasons or 1 season in particular which will return just that season in a list
    Returns:
        The list of seasons
    """
    if season == "all":
        season_list = range(datetime.now().year - 10, datetime.now().year - 1)
    else:
        season_list = [int(season)]

    return season_list


def get_elo_rankings(
    season: str = "all",
    conference: bool = False,
    recruiting: bool = False,
    margin_of_victory: bool = False,
) -> DataFrame:
    """
    Ranks all college football teams by their elo rating

    Parameters:
        season: str = "all"
            The season to get rankings for
        conference: bool = False
            Optionally weight elo by conference
        recruiting: bool = False
            Optionally weight elo by recruiting rank
        margin_of_victory: bool = False
            Optionally weight elo by margin of victory

    Returns:
        A dataframe containing all teams as ranked by elo

    """
    teams_df = build_teams_df(season, conference, recruiting)
    season_list = build_season_list(season)

    elo_col = teams_df["Elo"].copy()

    for season in season_list:
        games_df = data.load_games(season=season)
        elo_rankings_df = set_fcs(teams_df, games_df)

        # reset wins/losses
        elo_rankings_df["Wins"] = 0
        elo_rankings_df["Losses"] = 0

        weeks = games_df.week.unique()

        for i in weeks:
            elo_rankings_df = process_week_games(
                elo_rankings_df, games_df[games_df.week == i], margin_of_victory
            )

        # revert elo towards the mean
        # this is so past results aren't weighted as heavily as results from the current season
        # it also simulates player turnover, coach turnover, etc. between seasons
        elo_rankings_df["Elo"] = elo_rankings_df["Elo"].apply(
            revert_to_mean, args=(elo_rankings_df["Elo"].mean(),)
        )

    return elo_rankings_df


def revert_to_mean(x: int, mean: float) -> float:
    """
    Takes a value and a mean and reverts the value part of the way towards the mean:
        Formula: x +/- (0.7 * (diff_between x and mean))
    Parameters:
        x: int
            the value
        mean: float
            the mean of the series x resides in

    Returns:
        the new value of x after reverting towards mean

    """
    if x > mean:
        return x - (0.7 * (x - mean))
    else:
        return x + (0.7 * (mean - x))

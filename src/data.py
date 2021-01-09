from pathlib import Path

import numpy as np
import pandas as pd

path = Path(__file__).parent


def load_teams():
    teams_df = pd.read_csv(path / "../data/teams.csv")
    teams_df.drop(
        [
            "mascot",
            "abbreviation",
            "alt_name1",
            "alt_name2",
            "alt_name3",
            "division",
            "color",
            "alt_color",
            "logos[0]",
            "logos[1]",
        ],
        axis=1,
        inplace=True,
    )
    teams_df = teams_df.append(
        {
            "id": 9999,
            "school": "FCS",
        },
        ignore_index=True,
    )

    # every team starts with 0 wins, 0 losses
    teams_df["wins"] = 0
    teams_df["losses"] = 0

    # starting Elo is 1500
    # starting Elo for FCS team placeholder is 1000
    # (it's embarrassing to lose to an FCS team)
    teams_df["Elo"] = 1500
    teams_df.at[130, "Elo"] = 1000

    teams_df.columns = ["ID", "School", "Conference", "Wins", "Losses", "Elo"]

    rankings_df = load_rankings()

    # merge rankings df to get CFP actual ranks
    teams_df = teams_df.merge(rankings_df, how="left", on="School")

    teams_df.set_index("ID", inplace=True)

    # conversion shenanigans
    # this is to represent unranked teams as "NR"
    teams_df = teams_df.replace(np.nan, 0)
    teams_df["CFP Ranking"] = teams_df["CFP Ranking"].astype(int).astype(str)
    teams_df = teams_df.replace("0", "NR")

    return teams_df


def load_rankings():
    rankings_df = pd.read_csv(path / "../data/rankings.csv")

    rankings_df = rankings_df[rankings_df["week"] == 16]
    rankings_df = rankings_df[rankings_df["poll"] == "Playoff Committee Rankings"]

    rankings_df.drop(
        [
            "conference",
            "firstPlaceVotes",
            "season",
            "seasonType",
            "week",
            "poll",
            "points",
        ],
        axis=1,
        inplace=True,
    )

    rankings_df.columns = ["CFP Ranking", "School"]

    return rankings_df


def load_games(season):
    games_df = pd.DataFrame()

    season_path = "../data/games" + str(season) + ".csv"
    games_df = pd.read_csv(path / season_path)

    games_df.drop(
        [
            "start_date",
            "start_time_tbd",
            "neutral_site",
            "attendance",
            "venue_id",
            "venue",
            "home_conference",
            "away_conference",
            "home_line_scores[0]",
            "home_line_scores[1]",
            "home_line_scores[2]",
            "home_line_scores[3]",
            "home_post_win_prob",
            "away_line_scores[0]",
            "away_line_scores[1]",
            "away_line_scores[2]",
            "away_line_scores[3]",
            "away_post_win_prob",
            "excitement_index",
            "mascot",
            "abbreviation",
            "conference",
        ],
        axis=1,
        inplace=True,
        errors="ignore",
    )

    games_df.dropna(inplace=True)

    return games_df


def load_recruiting():
    recruit_df = pd.read_csv(path / "../data/recruiting2016.csv")

    for season in range(2017, 2021):
        season_path = "../data/recruiting" + str(season) + ".csv"
        df = pd.read_csv(path / season_path)

        recruit_df = pd.concat([recruit_df, df])

    recruit_df.drop(
        [
            "year",
            "rank",
        ],
        axis=1,
        inplace=True,
        errors="ignore",
    )

    recruit_df = recruit_df.groupby(["team"]).mean()

    return recruit_df

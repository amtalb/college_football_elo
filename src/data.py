import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

URL = "https://api.collegefootballdata.com/"
CURRENT_SEASON = "2020"


def load_teams(season=CURRENT_SEASON):
    team_endpoint = "teams/fbs"
    params = {"year": season}
    res = requests.request("GET", URL + team_endpoint, params=params)
    teams_df = pd.json_normalize(res.json())

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
            "logos",
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

    rankings_df = load_rankings(season=season)

    # merge rankings df to get CFP actual ranks
    teams_df = teams_df.merge(rankings_df, how="left", on="School")

    teams_df.set_index("ID", inplace=True)

    # conversion shenanigans
    # this is to represent unranked teams as "NR"
    teams_df = teams_df.replace(np.nan, 0)
    teams_df["AP Ranking"] = teams_df["AP Ranking"].astype(int).astype(str)
    teams_df = teams_df.replace("0", "NR")

    return teams_df


def load_rankings(season=CURRENT_SEASON):
    params = {"year": season, "seasonType": "postseason"}
    endpoint = "rankings"
    r = requests.request("GET", URL + endpoint, params=params)
    rankings_df = pd.json_normalize(
        r.json(),
        record_path=["polls", "ranks"],
        meta=["season", "seasonType", "week", ["polls", "poll"]],
    )

    rankings_df = rankings_df[rankings_df["polls.poll"] == "AP Top 25"]

    rankings_df.drop(
        [
            "conference",
            "firstPlaceVotes",
            "season",
            "seasonType",
            "week",
            "polls.poll",
            "points",
        ],
        axis=1,
        inplace=True,
    )

    rankings_df.columns = ["AP Ranking", "School"]

    return rankings_df


def load_games(season=CURRENT_SEASON):
    games_df = pd.DataFrame()

    for seasonType in ["regular", "postseason"]:
        params = {"year": season, "seasonType": seasonType}
        endpoint = "games"
        r = requests.request("GET", URL + endpoint, params=params)
        df = pd.json_normalize(r.json())

        df.drop(
            [
                "start_date",
                "start_time_tbd",
                "neutral_site",
                "attendance",
                "venue_id",
                "venue",
                "home_conference",
                "away_conference",
                "home_line_scores",
                "home_post_win_prob",
                "away_line_scores",
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
        if seasonType == "postseason":
            df["week"] += games_df.week.max()

        games_df = pd.concat([games_df, df], axis=0)

    games_df.dropna(inplace=True)

    return games_df


def load_recruiting(season=CURRENT_SEASON):
    recruit_df = pd.DataFrame()

    for season in range(int(season) - 4, int(season) + 1):
        params = {"year": season}
        endpoint = "recruiting/teams"
        r = requests.request("GET", URL + endpoint, params=params)
        df = pd.json_normalize(r.json())

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

    # convert points column to numeric
    recruit_df["points"] = pd.to_numeric(recruit_df["points"])

    # average recruiting score over the previous 5 seasons
    recruit_df = recruit_df.groupby(["team"]).mean()

    return recruit_df

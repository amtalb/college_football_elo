import json
from pathlib import Path
from datetime import datetime
import os

import numpy as np
import pandas as pd
from pandas import DataFrame
import requests
from dotenv import load_dotenv

MOST_RECENT_FULL_SEASON = datetime.now().year - 1

load_dotenv()


def request_cfb_api(
    endpoint: str,
    params: dict[str, str],
    record_path: list[str] = None,
    meta: list[str] = None,
) -> DataFrame:
    """
    Calls the CollegeFootballData API and normalizes the JSON results into a Pandas DataFrame. Loads API key from env file
    Params:
        endpoint: str
            the API endpoint
        params: dict[str, str]
            a dictionary of request parameters
        record_path: list[str] = None
            an option to be fed into pandas.json_normalize()
        meta: list[str] = None
            an option to be fed into pandas.json_normalize()
    Returns:
        Pandas DataFrame with requested data in tabular form
    """
    api_token = {"authorization": f"Bearer {os.getenv('API_KEY')}"}
    res = requests.get(
        url="https://api.collegefootballdata.com/" + endpoint,
        headers=api_token,
        params=params,
    )
    return pd.json_normalize(res.json(), record_path=record_path, meta=meta)


def add_fcs_schools(df: DataFrame) -> DataFrame:
    """
    Adds an entry to the provided DataFrame to represent an FCS opponent placeholder
    Params:
        df: DataFrame
            the df to apply the transformation to
    Returns:
        Pandas DataFrame with an placeholder for FCS teams added
    """
    df.loc[-1] = {
        "id": 9999,
        "school": "FCS",
    }
    df.index = df.index + 1
    return df.sort_index()


def team_df_setup(df: DataFrame) -> DataFrame:
    """
    Runs some preprocessing on the teams DataFrame by setting FCS teams, wins, losses, and Elo to default values
    Params:
        df: DataFrame
            The teams DataFrame
    Returns:
        The teams DataFrame with FCS teams, wins, losses, and Elo set correctly
    """
    # add FCS opponent placeholder
    df = add_fcs_schools(df)

    # every team starts with 0 wins, 0 losses
    df["wins"] = 0
    df["losses"] = 0

    # starting Elo is 1500
    # starting Elo for FCS team placeholder is 1000
    # (it's embarrassing to lose to an FCS team)
    df["Elo"] = 1500
    df.at[130, "Elo"] = 1000

    return df


def load_teams(season: int = MOST_RECENT_FULL_SEASON) -> DataFrame:
    """
    Calls the CollegeFootballData API and gets team data in a Pandas DataFrame
    Params:
        season: int = MOST_RECENT_FULL_SEASON
            The season to request data from
    Returns:
        Pandas DataFrame with the requested season's team data
    """
    # API call
    teams_df = request_cfb_api("teams/fbs", {"year": season})

    # drop unnecessary columns
    teams_df = teams_df[["id", "school", "conference"]]

    # do some preprocessing
    teams_df = team_df_setup(teams_df)

    # rename columns
    teams_df.columns = ["ID", "School", "Conference", "Wins", "Losses", "Elo"]

    # merge with rankings df to get CFP actual ranks
    teams_df = teams_df.merge(
        load_rankings(season=season), how="left", on="School"
    ).set_index("ID")

    # conversion shenanigans
    teams_df = teams_df.replace(np.nan, 0)
    teams_df["AP Ranking"] = teams_df["AP Ranking"].astype(int).astype(str)
    # this is to represent unranked teams as "NR"
    teams_df = teams_df.replace("0", "NR")

    return teams_df


def load_rankings(season: int = MOST_RECENT_FULL_SEASON) -> DataFrame:
    """
    Calls the CollegeFootballData API and gets ranking data in a Pandas DataFrame
    Params:
        season: int = MOST_RECENT_FULL_SEASON
            The season to request data from
    Returns:
        Pandas DataFrame with the requested season's ranking data
    """
    # API call
    return_df = request_cfb_api(
        "rankings", {"year": season, "seasonType": "postseason"}
    )

    # sort to only AP Top 25 teams
    rankings_df = pd.DataFrame(
        [x[0]["ranks"] for x in return_df["polls"] if x[0]["poll"] == "AP Top 25"][0]
    )

    # drop unnecessary columns
    rankings_df = rankings_df[["rank", "school"]]

    # rename columns
    rankings_df.columns = ["AP Ranking", "School"]

    return rankings_df


def load_games(season: int = MOST_RECENT_FULL_SEASON) -> DataFrame:
    """
    Calls the CollegeFootballData API and gets game data in a Pandas DataFrame
    Params:
        season: int = MOST_RECENT_FULL_SEASON
            The season to request data from
    Returns:
        Pandas DataFrame with the requested season's game data
    """
    # init empty df
    games_df = pd.DataFrame()

    # loop over regular and postseason
    for seasonType in ["regular", "postseason"]:
        # API call
        df = request_cfb_api("games", {"year": season, "seasonType": seasonType})

        # drop unnecessary columns
        df = df[
            [
                "id",
                "season",
                "week",
                "season_type",
                "home_id",
                "home_team",
                "home_points",
                "away_id",
                "away_team",
                "away_points",
            ]
        ]

        # if the game is a postseason game, make it the last week
        if seasonType == "postseason":
            df["week"] += games_df.week.max()
        # join this to the main games_df
        games_df = pd.concat([games_df, df], axis=0)

    games_df = games_df.dropna()

    return games_df


def load_recruiting(season: int = MOST_RECENT_FULL_SEASON) -> DataFrame:
    """
    Calls the CollegeFootballData API and gets recruiting data in a Pandas DataFrame
    Params:
        season: int = MOST_RECENT_FULL_SEASON
            The season to request data from
    Returns:
        Pandas DataFrame with the requested season's recruiting data
    """
    # init empty df
    recruit_df = pd.DataFrame()

    # loop over the last 5 seasons, getting recruiting data and appending it to the df
    for season in range(int(season) - 4, int(season) + 1):
        # API call
        df = request_cfb_api("recruiting/teams", {"year": season})
        # join to main df
        recruit_df = pd.concat([recruit_df, df])

    # drop unnecessary columns
    recruit_df = recruit_df.drop(
        [
            "year",
            "rank",
        ],
        axis=1,
        errors="ignore",
    )

    # convert points column to numeric
    recruit_df["points"] = pd.to_numeric(recruit_df["points"])

    # average recruiting score over the previous 5 seasons
    recruit_df = recruit_df.groupby(["team"]).mean()

    return recruit_df

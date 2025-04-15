import requests
import pandas as pd
import time

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://www.nba.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

URL = "https://stats.nba.com/stats/leaguedashplayerstats"

PARAMS = {
    "Season": "2023-24",
    "SeasonType": "Regular Season",
    "MeasureType": "Base",         # Basic stats
    "PerMode": "PerGame",          # PerGame or Totals
    "LeagueID": "00",
    "LastNGames": "0",
    "Month": "0",
    "OpponentTeamID": "0",
    "PORound": "0",
    "Period": "0",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "PlusMinus": "N",
    "Rank": "N",
    "SeasonSegment": "",
    "ShotClockRange": "",
    "StarterBench": "",
    "TeamID": "0",
    "TwoWay": "0",
    "VsConference": "",
    "VsDivision": ""
}


def fetch_nba_stats(season="2023-24"):
    try:
        time.sleep(1)
        params = PARAMS.copy()
        params["Season"] = season
        response = requests.get(URL, headers=HEADERS, params=params)

        data = response.json()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]

        df = pd.DataFrame(rows, columns=headers)
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NBA stats: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")
        raise


if __name__ == "__main__":
    df = fetch_nba_stats()
    print(df.head())
    print("✅ Fetched rows:", len(df))


def clean_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    # Drop exact duplicate rows
    df = df.drop_duplicates(subset=["PLAYER_ID"])

    # Remove rows with obviously broken data
    df = df[df["GP"] > 0]  # Must have played at least 1 game

    # Ensure percentages are within 0–1 (sometimes they appear as 100-based)
    df["FG_PCT"] = df["FG_PCT"].apply(lambda x: x if 0 <= x <= 1 else x / 100)
    df["FT_PCT"] = df["FT_PCT"].apply(lambda x: x if 0 <= x <= 1 else x / 100)

    # Normalize column names to match your PlayerStats table
    rename_map = {
        "PLAYER_ID": "player_id",
        "TEAM_ABBREVIATION": "team",
        "GP": "games_played",
        "MIN": "minutes_per_game",
        "PTS": "points_per_game",
        "REB": "rebounds_per_game",
        "AST": "assists_per_game",
        "STL": "steals_per_game",
        "BLK": "blocks_per_game",
        "TOV": "turnovers_per_game",
        "FG_PCT": "fg_pct",
        "FT_PCT": "ft_pct",
        "FG3M": "three_pm"
    }

    df = df.rename(columns=rename_map)

    # Keep only columns we want
    return df[list(rename_map.values())]

import sys
import os
import time
import datetime
import requests
import pandas as pd
from sqlalchemy.orm import Session

# Set project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import PlayerGameStats


HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer": "https://www.nba.com/",
    "Connection": "keep-alive"
}

URL = "https://stats.nba.com/stats/playergamelogs"

PARAMS = {
    "Season": "2023-24",
    "SeasonType": "Regular Season",
    "LeagueID": "00"
}


def fetch_player_game_logs(season="2023-24"):
    print(f"⏳ Fetching game logs for {season} from NBA stats API...")
    time.sleep(1)
    params = PARAMS.copy()
    params["Season"] = season
    response = requests.get(URL, headers=HEADERS, params=params)

    data = response.json()
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"]
    df = pd.DataFrame(rows, columns=headers)
    print(f"✅ Retrieved {len(df)} rows of player game logs.")
    return df


def normalize_game_log_data(df):
    df_clean = pd.DataFrame()
    df_clean["player_id"] = df["PLAYER_ID"]
    df_clean["game_date"] = pd.to_datetime(df["GAME_DATE"])
    df_clean["opponent_team"] = df["MATCHUP"].apply(lambda x: x.split(" ")[-1])
    df_clean["home_or_away"] = df["MATCHUP"].apply(lambda x: "H" if "vs." in x else "A")
    df_clean["minutes"] = df["MIN"]
    df_clean["points"] = df["PTS"]
    df_clean["rebounds"] = df["REB"]
    df_clean["assists"] = df["AST"]
    df_clean["steals"] = df["STL"]
    df_clean["blocks"] = df["BLK"]
    df_clean["turnovers"] = df["TOV"]
    df_clean["fgm"] = df["FGM"]
    df_clean["fga"] = df["FGA"]
    df_clean["ftm"] = df["FTM"]
    df_clean["fta"] = df["FTA"]
    df_clean["three_pm"] = df["FG3M"]
    df_clean["plus_minus"] = df["PLUS_MINUS"]
    
    # Calculate fantasy points using standard scoring
    df_clean["fantasy_points"] = (
        df_clean["points"] * 1.0 +
        df_clean["rebounds"] * 1.2 +
        df_clean["assists"] * 1.5 +
        df_clean["steals"] * 3.0 +
        df_clean["blocks"] * 3.0 +
        df_clean["turnovers"] * -1.0
    )
    
    df_clean["last_updated"] = datetime.datetime.utcnow()
    return df_clean


def insert_player_game_logs(df_clean):
    session: Session = SessionLocal()
    try:
        count = 0
        for _, row in df_clean.iterrows():
            record = PlayerGameStats(**row.to_dict())
            session.add(record)
            count += 1
        session.commit()
        print(f"✅ Inserted {count} game log records into player_game_stats.")
    except Exception as e:
        session.rollback()
        print("❌ Insert failed:", e)
    finally:
        session.close()


if __name__ == "__main__":
    df_raw = fetch_player_game_logs()
    df_clean = normalize_game_log_data(df_raw)
    insert_player_game_logs(df_clean)

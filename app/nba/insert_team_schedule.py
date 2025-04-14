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
from app.models.models import TeamSchedule

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer": "https://www.nba.com/",
    "Connection": "keep-alive"
}

URL = "https://stats.nba.com/stats/leaguegamefinder"

PARAMS = {
    "LeagueID": "00",
    "Season": "2023-24",
    "SeasonType": "Regular Season",
    "Sorter": "DATE",
    "Direction": "ASC",
    "PlayerOrTeam": "T"  # Team-level schedule
}


def fetch_team_schedule():
    print("⏳ Fetching team schedule from NBA stats API...")
    time.sleep(1)
    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    response.raise_for_status()

    data = response.json()
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"]
    df = pd.DataFrame(rows, columns=headers)
    print(f"✅ Retrieved {len(df)} team schedule rows.")
    return df


def normalize_team_schedule(df):
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df["home_or_away"] = df["MATCHUP"].apply(lambda x: "H" if "vs." in x else "A")
    df["opponent"] = df["MATCHUP"].apply(lambda x: x.split(" ")[-1])
    df["season"] = "2023-24"
    df["is_back_to_back"] = False  # Placeholder — we can backfill later
    df["is_high_volume_day"] = False  # Placeholder — same here

    df_clean = pd.DataFrame({
        "game_date": df["GAME_DATE"],
        "team": df["TEAM_ABBREVIATION"],
        "opponent_team": df["opponent"],
        "home_or_away": df["home_or_away"],
        "season": df["season"],
        "is_back_to_back": df["is_back_to_back"],
        "is_high_volume_day": df["is_high_volume_day"],
        "created_at": datetime.datetime.utcnow()
    })

    return df_clean


def insert_team_schedule(df_clean):
    session: Session = SessionLocal()
    try:
        count = 0
        for _, row in df_clean.iterrows():
            record = TeamSchedule(**row.to_dict())
            session.add(record)
            count += 1
        session.commit()
        print(f"✅ Inserted {count} schedule rows into team_schedule.")
    except Exception as e:
        session.rollback()
        print("❌ Insert failed:", e)
    finally:
        session.close()


if __name__ == "__main__":
    df_raw = fetch_team_schedule()
    df_clean = normalize_team_schedule(df_raw)
    insert_team_schedule(df_clean)

# app/nba/backfill_adp_into_player_season_info.py

from sqlalchemy.orm import Session
from sqlalchemy import update
import os
import sys
from thefuzz import process  # fuzzy matching
import pandas as pd

# Project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import Player, PlayerSeasonInfo

# Manual name corrections
manual_name_corrections = {
    "Doncic, Luka": "Luka Dončić",
    "Warren, TJ": "T.J. Warren",
    "Hernangomez, Guillermo": "Willy Hernangómez",
    "Saric, Dario": "Dario Šarić",
    "Mills, Patrick": "Patty Mills",
    "Dozier, P.J.": "P.J. Dozier",
    "Krejci, Vit": "Vít Krejčí",
    "Kanter, Enes": "Enes Freedom",
    "Pasecniks, Anzejs": "Anžejs Pasečņiks",
    "Claxton, Nicolas": "Nic Claxton",  # 'Nicolas' vs. 'Nic' in most DBs
    "Cancar, Vlatko": "Vlatko Čančar",
    "Nembhard, R.J.": "RJ Nembhard",
    "Vezenkov, Aleksandar": "Sasha Vezenkov",  # Commonly referred to as 'Sasha'
}

SEASONS = [
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
]

def load_adp_data(season: str) -> pd.DataFrame:
    formatted_season = season.replace("-", "_")
    filepath = f"app/data/adp/{formatted_season}_adp.csv"
    df = pd.read_csv(filepath)

    # Drop repeated header rows if any
    df = df[df["Player"] != "Player"]

    # Keep only relevant columns
    df = df[["Player", "Rank"]]

    return df

def backfill_adp(season: str, use_fuzzy: bool = True):
    session: Session = SessionLocal()

    # Load ADP from csv
    adp_df = load_adp_data(season)

    # Load players from DB
    players = session.query(Player).all()
    player_map = {p.name: p.player_id for p in players}

    matched = 0
    unmatched = []

    for _, row in adp_df.iterrows():
        csv_name = row["Player"]
        adp_rank = row["Rank"]

        # Manual fix
        csv_name_corrected = manual_name_corrections.get(csv_name, csv_name)

        # Try exact match first
        matched_player_id = player_map.get(csv_name_corrected)

        if not matched_player_id and use_fuzzy:
            # Fuzzy match fallback
            best_match, score = process.extractOne(csv_name_corrected, player_map.keys())
            if score > 80:
                matched_player_id = player_map[best_match]
            else:
                unmatched.append(csv_name)
                continue

        if matched_player_id:
            session.execute(
                update(PlayerSeasonInfo)
                .where(PlayerSeasonInfo.player_id == matched_player_id)
                .where(PlayerSeasonInfo.season == season)
                .values(adp=adp_rank)
            )
            matched += 1

    session.commit()
    session.close()

    print(f"✅ Backfill complete for {season}")
    print(f"🔍 Matched {matched} players")
    if unmatched:
        print(f"⚠️ Unmatched players: {unmatched}")

if __name__ == "__main__":
    for season in SEASONS:
        backfill_adp(season=season, use_fuzzy=True)

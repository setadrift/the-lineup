# app/nba/backfill_adp_into_player_season_info.py

import os
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import update
from dotenv import load_dotenv
from fuzzywuzzy import process

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import Player, PlayerSeasonInfo
from app.nba.load_adp_csv_to_memory import load_adp_data

# Load env
load_dotenv()

def backfill_adp(season: str = "2022-23", use_fuzzy: bool = True):
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

        # Try exact match first
        matched_player_id = player_map.get(csv_name)

        if not matched_player_id and use_fuzzy:
            # If no exact match, fuzzy match
            best_match, score = process.extractOne(csv_name, player_map.keys())
            if score > 80:
                matched_player_id = player_map[best_match]
            else:
                unmatched.append(csv_name)
                continue

        if matched_player_id:
            # Update player_season_info
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
    backfill_adp(season="2022-23", use_fuzzy=True)

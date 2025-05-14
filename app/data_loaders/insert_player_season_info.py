import sys
import os
import datetime
import pandas as pd
from sqlalchemy.orm import Session

# Set up path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import PlayerSeasonInfo, PlayerStats

SEASONS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

def build_season_info_rows(session: Session, season: str):
    # Use player_stats to determine active players that season
    stats = session.query(PlayerStats).filter(PlayerStats.season == season).all()
    rows = []
    for s in stats:
        row = PlayerSeasonInfo(
            player_id=s.player_id,
            season=season,
            adp=999,  # Placeholder
            injury_notes=None,  # Placeholder
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        rows.append(row)
    return rows

def insert_season_info(seasons):
    session: Session = SessionLocal()
    try:
        for season in seasons:
            print(f"🔄 Inserting season info for {season}...")
            rows = build_season_info_rows(session, season)

            # Delete any existing rows for this season
            session.query(PlayerSeasonInfo).filter(PlayerSeasonInfo.season == season).delete()

            for row in rows:
                session.add(row)
            session.commit()
            print(f"✅ Inserted {len(rows)} player_season_info rows for {season}")
    except Exception as e:
        session.rollback()
        print("❌ Failed:", e)
    finally:
        session.close()

if __name__ == "__main__":
    insert_season_info(SEASONS)

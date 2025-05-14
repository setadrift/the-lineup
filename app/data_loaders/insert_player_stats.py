import sys
import os
import pandas as pd
from sqlalchemy.orm import Session

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

import datetime
from app.db.connection import SessionLocal
from app.models.models import PlayerStats
from app.data_loaders.fetch_season_stats import fetch_nba_stats, clean_player_stats


def insert_player_stats(df, season="2023-24"):
    session: Session = SessionLocal()

    try:
        for _, row in df.iterrows():
            stat = PlayerStats(
                player_id=row["player_id"],
                season=season,
                team=row["team"],
                games_played=row["games_played"],
                minutes_per_game=row["minutes_per_game"],
                points_per_game=row["points_per_game"],
                rebounds_per_game=row["rebounds_per_game"],
                assists_per_game=row["assists_per_game"],
                steals_per_game=row["steals_per_game"],
                blocks_per_game=row["blocks_per_game"],
                turnovers_per_game=row["turnovers_per_game"],
                fg_pct=row["fg_pct"],
                ft_pct=row["ft_pct"],
                three_pm=row["three_pm"],
                last_updated=datetime.datetime.utcnow(),
            )

            # Upsert logic: delete existing record for this player + season first
            session.query(PlayerStats).filter(
                PlayerStats.player_id == stat.player_id,
                PlayerStats.season == season
            ).delete()

            session.add(stat)

        session.commit()
        print(f"✅ Inserted {len(df)} PlayerStats rows into DB.")
    except Exception as e:
        session.rollback()
        print("❌ Failed to insert PlayerStats:", e)
    finally:
        session.close()


if __name__ == "__main__":
    df_cleaned = clean_player_stats(fetch_nba_stats())
    insert_player_stats(df_cleaned)

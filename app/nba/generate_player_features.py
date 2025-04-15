import sys
import os
import datetime
import pandas as pd
from scipy.stats import zscore
from sqlalchemy.orm import Session

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import PlayerStats, PlayerFeatures


def fetch_player_stats(session: Session, season: str):
    players = session.query(PlayerStats).filter(PlayerStats.season == season).all()
    data = [vars(p) for p in players]
    df = pd.DataFrame(data).drop(columns=["_sa_instance_state"])
    return df


def compute_z_scores(df: pd.DataFrame):
    stat_cols = {
        "points_per_game": "z_points",
        "rebounds_per_game": "z_rebounds",
        "assists_per_game": "z_assists",
        "steals_per_game": "z_steals",
        "blocks_per_game": "z_blocks",
        "turnovers_per_game": "z_turnovers",  # Invert later
        "fg_pct": "z_fg_pct",
        "ft_pct": "z_ft_pct",
        "three_pm": "z_three_pm"
    }

    z_df = pd.DataFrame()
    z_df["player_id"] = df["player_id"]
    z_df["season"] = df["season"]

    for raw_col, z_col in stat_cols.items():
        if raw_col == "turnovers_per_game":
            z_df[z_col] = -1 * zscore(df[raw_col].fillna(0))
        else:
            z_df[z_col] = zscore(df[raw_col].fillna(0))

    z_score_cols = list(stat_cols.values())
    z_df["total_z_score"] = z_df[z_score_cols].sum(axis=1)
    z_df["created_at"] = datetime.datetime.utcnow()
    z_df["updated_at"] = datetime.datetime.utcnow()

    return z_df


def insert_features(df: pd.DataFrame):
    session: Session = SessionLocal()
    try:
        for _, row in df.iterrows():
            record = PlayerFeatures(**row.to_dict())
            session.add(record)
        session.commit()
        print(f"✅ Inserted {len(df)} feature rows into player_features table.")
    except Exception as e:
        session.rollback()
        print("❌ Failed to insert features:", e)
    finally:
        session.close()



if __name__ == "__main__":
    session = SessionLocal()
    seasons = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

    for season in seasons:
        print(f"📈 Generating player features for {season}...")
        df_stats = fetch_player_stats(session, season)
        if df_stats.empty:
            print(f"⚠️ Skipping {season} — no player stats found.")
            continue
        df_features = compute_z_scores(df_stats)
        insert_features(df_features)

    session.close()

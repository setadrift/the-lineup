"""
Generate player features and z-scores from raw statistics.
"""

import datetime
import pandas as pd
from scipy.stats import zscore
from typing import Optional

from app.models.models import PlayerStats, PlayerFeatures
from app.utils.db import get_db, safe_commit, batch_upsert
from app.utils.validation import validate_season_format, validate_player_stats
from app.utils.logging import setup_logger, log_execution_time
from app.config.constants import PACE_FACTORS, FANTASY_SCORING

# Set up logger
logger = setup_logger(__name__)

def fetch_player_stats(season: str) -> pd.DataFrame:
    """
    Fetch player stats from database for a given season.
    
    Args:
        season (str): Season in format '2023-24'
        
    Returns:
        pd.DataFrame: Player stats DataFrame
        
    Raises:
        ValueError: If season format is invalid
    """
    if not validate_season_format(season):
        raise ValueError(f"Invalid season format: {season}. Expected format: YYYY-YY")
        
    with get_db() as session:
        players = session.query(PlayerStats).filter(PlayerStats.season == season).all()
        data = [vars(p) for p in players]
        df = pd.DataFrame(data).drop(columns=["_sa_instance_state"])
        
        logger.info(f"✅ Fetched {len(df)} player stats records for {season}")
        return df

def compute_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute z-scores for player statistics.
    
    Args:
        df (pd.DataFrame): Player stats DataFrame
        
    Returns:
        pd.DataFrame: Z-score DataFrame
    """
    # Validate input DataFrame
    errors = validate_player_stats(df)
    if errors:
        logger.error("❌ Player stats validation failed", extra={"errors": errors})
        raise ValueError(f"Player stats validation failed: {errors}")

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
    
    now = datetime.datetime.utcnow()
    z_df["created_at"] = now
    z_df["updated_at"] = now

    logger.info(f"✅ Computed z-scores for {len(z_df)} players")
    return z_df

def insert_features(df: pd.DataFrame, batch_size: int = 100) -> bool:
    """
    Insert player features into database.
    
    Args:
        df (pd.DataFrame): Features DataFrame
        batch_size (int): Number of records per batch
        
    Returns:
        bool: True if successful, False if failed
    """
    records = [PlayerFeatures(**row.to_dict()) for _, row in df.iterrows()]
    
    with get_db() as session:
        success = batch_upsert(session, PlayerFeatures, records, batch_size)
        
        if success:
            logger.info(f"✅ Inserted {len(records)} feature records")
        else:
            logger.error("❌ Failed to insert features")
        
        return success

if __name__ == "__main__":
    logger.info("🚀 Starting feature generation...")
    
    seasons = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
    
    for season in seasons:
        try:
            import time
            start_time = time.time()
            
            logger.info(f"📈 Processing {season}...")
            df_stats = fetch_player_stats(season)
            
            if df_stats.empty:
                logger.warning(f"⚠️ Skipping {season} — no player stats found.")
                continue
                
            df_features = compute_z_scores(df_stats)
            success = insert_features(df_features)
            
            if success:
                log_execution_time(logger, start_time, f"Processed {season}")
                
        except Exception as e:
            logger.error(f"❌ Failed to process {season}: {e}", exc_info=True)

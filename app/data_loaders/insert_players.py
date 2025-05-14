"""
Insert or update player records in the database.
"""

import datetime
from typing import List
import pandas as pd

from app.models.models import Player
from app.utils.db import get_db, safe_commit, batch_upsert
from app.utils.data_cleaning import clean_player_name, map_position
from app.utils.logging import setup_logger
from app.data_loaders.fetch_season_stats import fetch_nba_stats

# Set up logger
logger = setup_logger(__name__)

def extract_player_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and clean player data from raw NBA stats.
    
    Args:
        df_raw (pd.DataFrame): Raw NBA stats DataFrame
        
    Returns:
        pd.DataFrame: Cleaned player DataFrame
    """
    # Extract only available fields from the NBA stats API
    players_df = df_raw[["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"]].drop_duplicates()
    
    # Clean player names and map positions
    players_df["name"] = players_df["PLAYER_NAME"].apply(clean_player_name)
    players_df["position"] = None  # Will be updated by backfill_positions.py
    
    # Rename columns
    players_df.columns = ["player_id", "raw_name", "team", "position"]
    players_df = players_df.drop(columns=["raw_name"])
    
    logger.info(f"✅ Extracted {len(players_df)} unique player records")
    return players_df

def create_player_records(df_players: pd.DataFrame) -> List[Player]:
    """
    Create Player model instances from DataFrame.
    
    Args:
        df_players (pd.DataFrame): Player DataFrame
        
    Returns:
        List[Player]: List of Player model instances
    """
    now = datetime.datetime.utcnow()
    
    records = []
    for _, row in df_players.iterrows():
        player = Player(
            player_id=row["player_id"],
            name=row["name"],
            team=row["team"],
            position=row["position"],
            created_at=now,
            updated_at=now,
        )
        records.append(player)
    
    return records

def insert_players(df_players: pd.DataFrame, batch_size: int = 100) -> bool:
    """
    Insert or update player records in batches.
    
    Args:
        df_players (pd.DataFrame): Player DataFrame
        batch_size (int): Number of records per batch
        
    Returns:
        bool: True if successful, False if failed
    """
    with get_db() as session:
        try:
            records = create_player_records(df_players)
            success = batch_upsert(session, Player, records, batch_size)
            
            if success:
                logger.info(f"✅ Successfully inserted {len(records)} player records")
            else:
                logger.error("❌ Failed to insert player records")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error inserting players: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Starting player data insertion...")
    df_raw = fetch_nba_stats()
    df_players = extract_player_data(df_raw)
    insert_players(df_players)

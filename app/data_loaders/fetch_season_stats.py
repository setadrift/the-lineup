"""
Fetch and clean NBA season statistics.
"""

import pandas as pd
from typing import Optional

from app.utils.api import make_nba_request
from app.utils.validation import validate_season_format, validate_player_stats
from app.utils.logging import setup_logger, log_execution_time, log_error_with_context
from app.config.constants import FANTASY_SCORING

# Set up logger
logger = setup_logger(__name__)

def fetch_nba_stats(season: str = "2023-24") -> pd.DataFrame:
    """
    Fetch player stats from NBA API for a given season.
    
    Args:
        season (str): Season in format '2023-24'
        
    Returns:
        pd.DataFrame: Raw stats data
        
    Raises:
        ValueError: If season format is invalid
    """
    if not validate_season_format(season):
        raise ValueError(f"Invalid season format: {season}. Expected format: YYYY-YY")

    params = {
        "Season": season,
        "SeasonType": "Regular Season",
        "MeasureType": "Base",
        "PerMode": "PerGame",
        "LeagueID": "00"
    }
    
    try:
        import time
        start_time = time.time()
        
        response = make_nba_request("leaguedashplayerstats", params)
        
        headers = response["resultSets"][0]["headers"]
        rows = response["resultSets"][0]["rowSet"]
        
        df = pd.DataFrame(rows, columns=headers)
        
        log_execution_time(logger, start_time, f"Fetched NBA stats for {season}")
        logger.info(f"✅ Retrieved {len(df)} player records")
        
        return df
        
    except Exception as e:
        log_error_with_context(
            logger,
            e,
            context={
                "operation": "fetch_nba_stats",
                "season": season,
                "params": params
            }
        )
        raise

def clean_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize player stats data.
    
    Args:
        df (pd.DataFrame): Raw stats DataFrame
        
    Returns:
        pd.DataFrame: Cleaned stats DataFrame
        
    Raises:
        ValueError: If DataFrame fails validation
    """
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
    df = df[list(rename_map.values())]
    
    # Validate the cleaned DataFrame
    errors = validate_player_stats(df)
    if errors:
        logger.error("❌ Player stats validation failed", extra={"errors": errors})
        raise ValueError(f"Player stats validation failed: {errors}")
    
    logger.info(f"✅ Cleaned & normalized {len(df)} player records")
    return df

if __name__ == "__main__":
    df = fetch_nba_stats()
    df_clean = clean_player_stats(df)
    print(df_clean.head())
    print("✅ Cleaned & normalized rows:", len(df_clean))

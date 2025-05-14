"""
Update player stats from NBA API and compute fantasy features.
"""

from datetime import datetime
from typing import List, Dict, Optional

from app.utils.db import get_db, batch_upsert
from app.utils.api import make_nba_request
from app.utils.validation import validate_season_format, validate_player_stats
from app.utils.logging import setup_logger, log_execution_time
from app.models.models import Player, PlayerStats
from app.config.settings import CURRENT_SEASON

# Set up logger
logger = setup_logger(__name__)

def fetch_current_stats() -> List[Dict]:
    """
    Fetch current season stats from NBA API.
    
    Returns:
        List[Dict]: List of player stats dictionaries
        
    Raises:
        Exception: If API request fails
    """
    try:
        if not validate_season_format(CURRENT_SEASON):
            raise ValueError(f"Invalid season format in settings: {CURRENT_SEASON}")
            
        logger.info(f"📊 Fetching current season stats for {CURRENT_SEASON}")
        
        response = make_nba_request(
            endpoint="leaguedashplayerstats",
            params={
                "Season": CURRENT_SEASON,
                "PerMode": "PerGame",
                "LastNGames": 0,
                "SeasonType": "Regular Season"
            }
        )
        
        if not response or 'resultSets' not in response:
            raise ValueError("Invalid response from NBA API")
            
        raw_stats = response['resultSets'][0]['rowSet']
        headers = response['resultSets'][0]['headers']
        
        stats = []
        for row in raw_stats:
            stat = dict(zip(headers, row))
            stats.append({
                'player_id': stat['PLAYER_ID'],
                'season': CURRENT_SEASON,
                'games_played': stat['GP'],
                'minutes_per_game': stat['MIN'],
                'points_per_game': stat['PTS'],
                'rebounds_per_game': stat['REB'],
                'assists_per_game': stat['AST'],
                'steals_per_game': stat['STL'],
                'blocks_per_game': stat['BLK'],
                'turnovers_per_game': stat['TOV'],
                'three_pm': stat['FG3M'],
                'fg_pct': stat['FG_PCT'],
                'ft_pct': stat['FT_PCT'],
                'updated_at': datetime.utcnow()
            })
            
        logger.info(f"✅ Successfully fetched stats for {len(stats)} players")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch current stats: {e}", exc_info=True)
        raise

def update_player_stats(stats: List[Dict]) -> None:
    """
    Update player stats in database.
    
    Args:
        stats (List[Dict]): List of player stats to update
        
    Raises:
        Exception: If database update fails
    """
    try:
        logger.info(f"💾 Updating stats for {len(stats)} players")
        
        # Validate stats before processing
        stats_df = pd.DataFrame(stats)
        if not validate_player_stats(stats_df):
            raise ValueError("Invalid player stats data")
            
        with get_db() as session:
            # Get existing player IDs
            existing_ids = {
                p[0] for p in session.query(Player.player_id).all()
            }
            
            # Filter stats for existing players
            valid_stats = [
                s for s in stats 
                if s['player_id'] in existing_ids
            ]
            
            if len(valid_stats) < len(stats):
                logger.warning(
                    f"⚠️ Skipping {len(stats) - len(valid_stats)} players not in database"
                )
            
            # Batch upsert stats
            batch_upsert(
                session=session,
                model=PlayerStats,
                records=valid_stats,
                unique_fields=['player_id', 'season']
            )
            
            logger.info(f"✅ Successfully updated stats for {len(valid_stats)} players")
            
    except Exception as e:
        logger.error(f"❌ Failed to update player stats: {e}", exc_info=True)
        raise

def main():
    """Update player stats and compute features."""
    try:
        import time
        start_time = time.time()
        
        # Fetch and update stats
        current_stats = fetch_current_stats()
        update_player_stats(current_stats)
        
        log_execution_time(logger, start_time, "Player stats update completed")
        
    except Exception as e:
        logger.error("❌ Player stats update failed", exc_info=True)
        raise

if __name__ == "__main__":
    main() 
# app/etl/backfill_positions.py

import time
import random
from typing import Optional

from sqlalchemy import update
from app.models.models import Player
from app.utils.api import make_nba_request
from app.utils.db import get_db, safe_commit
from app.utils.data_cleaning import map_position
from app.utils.logging import setup_logger, log_execution_time, log_error_with_context

# Set up logger
logger = setup_logger(__name__)

def fetch_player_position(player_id: int) -> Optional[str]:
    """
    Fetch player position from NBA API.
    
    Args:
        player_id (int): NBA player ID
        
    Returns:
        Optional[str]: Player position or None if not found
    """
    try:
        params = {"PlayerID": player_id}
        response = make_nba_request("commonplayerinfo", params)
        
        headers = response['resultSets'][0]['headers']
        row = response['resultSets'][0]['rowSet'][0]
        
        if "POSITION" in headers:
            position_index = headers.index("POSITION")
            raw_position = row[position_index]
            return map_position(raw_position) if raw_position else "UNK"
        else:
            logger.warning(f"⚠️ 'POSITION' field missing for Player ID {player_id}")
            return "UNK"
            
    except Exception as e:
        log_error_with_context(
            logger,
            e,
            context={
                "operation": "fetch_player_position",
                "player_id": player_id
            }
        )
        return "UNK"

def backfill_positions(batch_size: int = 50) -> bool:
    """
    Backfill missing player positions in batches.
    
    Args:
        batch_size (int): Number of players to process per batch
        
    Returns:
        bool: True if successful, False if any batch failed
    """
    with get_db() as session:
        try:
            # Get all players needing position updates
            players = session.query(Player).filter(
                (Player.position.is_(None)) | 
                (Player.position == "") | 
                (Player.position == "UNK")
            ).all()
            
            total_players = len(players)
            logger.info(f"🔍 Found {total_players} players to update")
            
            if not total_players:
                logger.info("✨ No players need position updates")
                return True
            
            # Process in batches
            for i in range(0, total_players, batch_size):
                batch = players[i:i + batch_size]
                logger.info(f"\n📦 Processing batch {i//batch_size + 1} of {(total_players + batch_size - 1)//batch_size}")
                
                batch_start = time.time()
                success = process_batch(session, batch)
                
                if not success:
                    logger.error(f"❌ Failed to process batch {i//batch_size + 1}")
                    return False
                
                log_execution_time(logger, batch_start, f"Processed batch {i//batch_size + 1}")
                
                # Random delay between batches (3-5 seconds)
                if i + batch_size < total_players:
                    delay = random.uniform(3, 5)
                    logger.info(f"😴 Sleeping for {delay:.1f} seconds before next batch...")
                    time.sleep(delay)
            
            logger.info("\n✅ Successfully completed position backfill!")
            return True
            
        except Exception as e:
            log_error_with_context(
                logger,
                e,
                context={
                    "operation": "backfill_positions",
                    "batch_size": batch_size
                }
            )
            return False

def process_batch(session, players: list) -> bool:
    """
    Process a batch of players to update their positions.
    
    Args:
        session: Database session
        players (list): List of Player instances to update
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        for idx, player in enumerate(players, 1):
            position = fetch_player_position(player.player_id)
            
            session.execute(
                update(Player)
                .where(Player.player_id == player.player_id)
                .values(position=position)
            )
            
            logger.info(f"[{idx}/{len(players)}] Updated {player.name} ({player.player_id}) to position: {position}")
            
            # Random delay between requests (1-2 seconds)
            time.sleep(1 + random.random())
        
        return safe_commit(session, f"Failed to commit batch of {len(players)} players")
        
    except Exception as e:
        log_error_with_context(
            logger,
            e,
            context={
                "operation": "process_batch",
                "batch_size": len(players)
            }
        )
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting position backfill...")
    success = backfill_positions()
    if not success:
        logger.error("❌ Position backfill failed")
        exit(1)

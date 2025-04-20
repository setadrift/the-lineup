# app/nba/backfill_positions.py

import os
import sys
import time
import random
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session
from sqlalchemy import update
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import Player

# Load environment variables
load_dotenv()

# NBA API headers with randomized user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://stats.nba.com/",
        "Connection": "keep-alive",
    }

COMMON_PLAYER_INFO_URL = "https://stats.nba.com/stats/commonplayerinfo"

# Configure retry strategy
retry_strategy = Retry(
    total=1,  # number of retries
    backoff_factor=0.5,  # quicker retry
    status_forcelist=[429, 500, 502, 503, 504],
)

# Create session with retry strategy
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

def fetch_player_position(player_id: int) -> str:
    """
    Fetches the true position of a player from NBA API using the correct header lookup.
    """
    try:
        params = {"PlayerID": player_id}
        response = session.get(
            COMMON_PLAYER_INFO_URL,
            headers=get_headers(),
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        headers = data['resultSets'][0]['headers']
        row = data['resultSets'][0]['rowSet'][0]
        
        if "POSITION" in headers:
            position_index = headers.index("POSITION")
            position = row[position_index]
            return position if position else "UNK"
        else:
            print(f"⚠️ 'POSITION' field missing for Player ID {player_id}")
            return "UNK"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch position for Player ID {player_id}: {e}")
        return "UNK"
    except Exception as e:
        print(f"❌ Unexpected error for Player ID {player_id}: {e}")
        return "UNK"


def backfill_positions(batch_size: int = 50):
    """
    Backfills player positions in batches with improved error handling.
    """
    db_session: Session = SessionLocal()
    
    try:
        # Get all players needing position updates
        players = db_session.query(Player).filter(
            (Player.position.is_(None)) | 
            (Player.position == "") | 
            (Player.position == "UNK")
        ).all()
        
        total_players = len(players)
        print(f"🔍 Found {total_players} players to update.")
        
        # Process in batches
        for i in range(0, total_players, batch_size):
            batch = players[i:i + batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1} of {(total_players + batch_size - 1)//batch_size}")
            
            for idx, player in enumerate(batch, 1):
                position = fetch_player_position(player.player_id)
                
                try:
                    db_session.execute(
                        update(Player)
                        .where(Player.player_id == player.player_id)
                        .values(position=position)
                    )
                    print(f"[{i + idx}/{total_players}] Updated {player.name} ({player.player_id}) to position: {position}")
                    
                    # Random delay between 1-2 seconds
                    time.sleep(1 + random.random())
                    
                except Exception as e:
                    print(f"❌ Failed to update DB for {player.name}: {e}")
                    continue
            
            # Commit after each batch
            db_session.commit()
            print(f"✅ Batch {i//batch_size + 1} completed!")
            
            # Longer delay between batches
            if i + batch_size < total_players:
                delay = random.uniform(3, 5)
                print(f"😴 Sleeping for {delay:.1f} seconds before next batch...")
                time.sleep(delay)
        
        print("\n✅ Successfully completed position backfill!")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Fatal error during backfill: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    backfill_positions()

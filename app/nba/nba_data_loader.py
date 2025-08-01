import requests
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.connection import SessionLocal
from app.db.models import Player  # make sure your Player model is defined and imported
import time

NBA_API_URL = "https://stats.nba.com/stats/commonallplayers?LeagueID=00&Season=2023-24&IsOnlyCurrentSeason=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true"
}


def fetch_active_players():
    response = requests.get(NBA_API_URL, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    headers = data['resultSets'][0]['headers']
    rows = data['resultSets'][0]['rowSet']
    
    # Convert each row to a dict using headers
    players = [dict(zip(headers, row)) for row in rows]
    return players


def normalize_player(row):
    position = fetch_player_position(row["PERSON_ID"])  # New
    time.sleep(0.5)  # 500ms sleep between requests to be safe
    
    return Player(
        player_id=row["PERSON_ID"],
        name=f"{row['DISPLAY_FIRST_LAST']}",
        team=row["TEAM_ABBREVIATION"] or "FA",
        position=position or "UNK",
        status="Active",
        bbm_rank=None,
        bbm_value=None,
        adp=None,
        games_played=0,
        injury_notes=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )



def insert_players_into_db(players):
    session: Session = SessionLocal()
    try:
        for player_data in players:
            player = normalize_player(player_data)
            
            # Upsert logic (update if exists)
            existing = session.query(Player).filter_by(player_id=player.player_id).first()
            if existing:
                existing.name = player.name
                existing.team = player.team
                existing.position = player.position
                existing.updated_at = datetime.utcnow()
            else:
                session.add(player)

        session.commit()
        print(f"✅ Inserted/updated {len(players)} players.")
    except Exception as e:
        session.rollback()
        print("❌ Failed to insert players:", e)
    finally:
        session.close()

COMMON_PLAYER_INFO_URL = "https://stats.nba.com/stats/commonplayerinfo"

def fetch_player_position(player_id):
    params = {
        "PlayerID": player_id
    }
    response = requests.get(COMMON_PLAYER_INFO_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    position = data['resultSets'][0]['rowSet'][0][14]  # Index of position
    return position


if __name__ == "__main__":
    players = fetch_active_players()
    insert_players_into_db(players)

import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.db.connection import SessionLocal
from app.models.models import Player
from app.nba.fetch_season_stats import fetch_nba_stats
import datetime


def extract_player_data(df_raw):
    # Extract only available fields from the NBA stats API
    players_df = df_raw[["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"]].drop_duplicates()
    players_df["PLAYER_POSITION"] = None  # placeholder, can update later
    players_df.columns = ["player_id", "name", "team", "position"]
    return players_df

def insert_players(df_players):
    session: Session = SessionLocal()

    try:
        for _, row in df_players.iterrows():
            player = Player(
                player_id=row["player_id"],
                name=row["name"],
                team=row["team"],
                position=row["position"],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )

            # Upsert logic: delete existing first
            session.query(Player).filter(Player.player_id == player.player_id).delete()
            session.add(player)

        session.commit()
        print(f"✅ Inserted {len(df_players)} players into DB.")
    except Exception as e:
        session.rollback()
        print("❌ Failed to insert players:", e)
    finally:
        session.close()


if __name__ == "__main__":
    df_raw = fetch_nba_stats()
    df_players = extract_player_data(df_raw)
    insert_players(df_players)

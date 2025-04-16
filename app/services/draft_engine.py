from typing import List, Dict
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_draft_recommendations(player_pool: List[Dict], user_team: List[Dict] = None, draft_config: Dict = None, top_n: int = 10) -> List[Dict]:
    """
    Returns top draft recommendations from a pool of players.

    Args:
        player_pool (List[Dict]): List of player dicts with keys:
            - name, player_id, position, adp, total_z_score, injury_status, available (bool)
        user_team (List[Dict], optional): Drafted players
        draft_config (Dict, optional): Future configs (e.g. punt strategies, category weighting)
        top_n (int): Number of recommendations to return

    Returns:
        List[Dict]: Top draft picks sorted by priority
    """
    user_team_ids = {p['player_id'] for p in user_team} if user_team else set()

    # Step 1: Filter out drafted players and unavailable players
    available_players = [
        p for p in player_pool
        if p.get("available", True) and p["player_id"] not in user_team_ids
    ]

    # Step 2: Remove duplicates by player_id
    seen_ids = set()
    deduped_players = []
    for player in available_players:
        if player["player_id"] not in seen_ids:
            seen_ids.add(player["player_id"])
            deduped_players.append(player)

    # Step 3: Remove or penalize injured players
    def injury_penalty(player):
        return -5 if player.get("injury_status") else 0

    # Step 4: Score players based on projected value + ADP + injury
    for player in deduped_players:
        adp = player.get("adp", 999)
        player["adp"] = adp if adp is not None else 999
        adp_weight = -0.05
        player["score"] = player["total_z_score"] + injury_penalty(player) + adp_weight * player["adp"]

    # Step 5: Sort by score descending
    sorted_players = sorted(deduped_players, key=lambda x: x["score"], reverse=True)

    return sorted_players[:top_n]

def fetch_player_data(season: str = "2023-24") -> List[Dict]:
    query = f"""
    SELECT 
        pf.player_id,
        p.name,
        p.position,
        psi.adp,
        psi.injury_notes AS injury_status,
        pf.total_z_score
    FROM player_features pf
    JOIN player_season_info psi ON pf.player_id = psi.player_id AND pf.season = psi.season
    JOIN players p ON pf.player_id = p.player_id
    WHERE pf.season = '{season}'
    """
    df = pd.read_sql(query, engine).drop_duplicates(subset=["player_id"])
    df["adp"] = df["adp"].fillna(999)
    df["available"] = True  # Assume all players are available for now
    return df.to_dict(orient="records")

if __name__ == "__main__":
    players = fetch_player_data()
    mock_team = [{"player_id": 1}]  # pretend Jokic is taken
    top_picks = get_draft_recommendations(players, user_team=mock_team)
    for p in top_picks:
        print(f"{p['name']} (Score: {p['score']:.2f}, ADP: {p['adp']})")

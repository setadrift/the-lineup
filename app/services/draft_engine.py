from typing import List, Dict
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Setup project path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Load player data
def fetch_player_pool(season: str = "2023-24") -> List[Dict]:
    query = f"""
    SELECT 
        pf.player_id,
        p.name,
        p.position,
        psi.adp,
        psi.injury_notes AS injury_status,
        pf.total_z_score
    FROM player_features pf
    JOIN players p ON pf.player_id = p.player_id
    LEFT JOIN player_season_info psi ON pf.player_id = psi.player_id AND pf.season = psi.season
    WHERE pf.season = '{season}'
    """
    df = pd.read_sql(query, engine)
    df = df.drop_duplicates(subset=["player_id"])
    df["adp"] = df["adp"].fillna(999)
    df["available"] = True  # Assume available unless drafted later
    df["position"] = df["position"].fillna("N/A")
    return df.to_dict(orient="records")

# Simple scoring function
def compute_draft_score(player: Dict) -> float:
    adp_weight = -0.05
    injury_penalty = -5 if player.get("injury_status") else 0

    score = (
        player.get("total_z_score", 0)
        + adp_weight * player.get("adp", 999)
        + injury_penalty
    )
    return score

# Recommendation engine
def get_recommendations(player_pool: List[Dict], drafted_players: List[int] = None, top_n: int = 10) -> List[Dict]:
    drafted_ids = set(drafted_players) if drafted_players else set()

    available_players = [
        p for p in player_pool
        if p.get("available", True) and p["player_id"] not in drafted_ids
    ]

    for player in available_players:
        player["score"] = compute_draft_score(player)

    sorted_players = sorted(available_players, key=lambda p: p["score"], reverse=True)
    return sorted_players[:top_n]

if __name__ == "__main__":
    player_pool = fetch_player_pool(season="2023-24")
    mock_drafted_players = []  # Update this as drafting progresses

    recommendations = get_recommendations(player_pool, drafted_players=mock_drafted_players)

    print("\n📈 Draft Recommendations:\n")
    for p in recommendations:
        print(f"{p['name']} (Score: {p['score']:.2f}, ADP: {p['adp']})")

def simulate_draft(num_teams=12, roster_size=14, season="2023-24"):
    player_pool = fetch_player_pool(season)
    drafted_players = set()
    
    # Initialize teams
    teams = {i: [] for i in range(1, num_teams + 1)}
    
    pick_order = list(range(1, num_teams + 1))
    round_number = 1

    for round_pick in range(roster_size):
        if round_number % 2 == 0:
            pick_order = list(reversed(pick_order))  # Snake draft reverses every round
        
        for team_id in pick_order:
            current_pick = len(drafted_players) + 1

            # Fetch recommendations
            recommendations = get_recommendations(player_pool, drafted_players, top_n=5)
            
            if not recommendations:
                print("No more players available!")
                break
            
            selected_player = recommendations[0]
            teams[team_id].append(selected_player)
            drafted_players.add(selected_player["player_id"])

            print(f"Round {round_number}, Team {team_id}: Drafted {selected_player['name']} (Score: {selected_player['score']:.2f}, ADP: {selected_player['adp']})")

        round_number += 1

    print("\n🏆 Draft complete!\n")

    # Show final rosters
    for team_id, roster in teams.items():
        print(f"\nTeam {team_id} Roster:")
        for player in roster:
            print(f"- {player['name']} (Position: {player['position']}, Score: {player['score']:.2f}, ADP: {player['adp']})")

if __name__ == "__main__":
    simulate_draft()

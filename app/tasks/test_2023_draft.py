# app/tasks/test_2023_draft.py

import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from app.db.connection import SessionLocal
from app.models.models import Player, PlayerStats

# --- Helper Functions ---

def load_adp_data():
    """Load and process ADP data, mapping player names to IDs from the database."""
    # Load ADP data
    adp_path = "app/data/adp/2023_24_adp.csv"
    adp_df = pd.read_csv(adp_path)
    
    # Clean up player names (remove commas and reorder first/last name)
    adp_df['clean_name'] = adp_df['Player'].apply(lambda x: ' '.join(reversed(x.split(', '))) if ', ' in x else x)
    
    # Get player ID mapping from database
    db_session = SessionLocal()
    try:
        players = db_session.query(Player.player_id, Player.name).all()
        player_map = {name: pid for pid, name in players}
        
        # Map player IDs
        adp_df['player_id'] = adp_df['clean_name'].map(player_map)
        
        # Keep only rows where we found a player_id match
        valid_players = adp_df.dropna(subset=['player_id'])
        
        if len(valid_players) < len(adp_df):
            print(f"⚠️ Warning: Could not find player_ids for {len(adp_df) - len(valid_players)} players")
            
        # Convert Rank to numeric ADP and select needed columns
        result = valid_players[['player_id', 'clean_name', 'Rank']].copy()
        result.columns = ['player_id', 'name', 'adp']
        
        return result
        
    finally:
        db_session.close()

def load_model_projections(db_session: Session):
    results = db_session.query(Player.player_id, Player.name, Player.projection).all()
    df = pd.DataFrame(results, columns=['player_id', 'name', 'projection'])
    return df

def load_actual_season_stats(db_session: Session):
    """Load actual season stats with player names from a join with Player table."""
    results = db_session.query(
        PlayerStats.player_id,
        Player.name,
        PlayerStats.points_per_game.label('points'),
        PlayerStats.rebounds_per_game.label('rebounds'),
        PlayerStats.assists_per_game.label('assists'),
        PlayerStats.steals_per_game.label('steals'),
        PlayerStats.blocks_per_game.label('blocks'),
        PlayerStats.three_pm.label('threes'),
        PlayerStats.turnovers_per_game.label('turnovers'),
        PlayerStats.fg_pct,
        PlayerStats.ft_pct
    ).join(
        Player, 
        Player.player_id == PlayerStats.player_id
    ).filter(
        PlayerStats.season == "2023-24"
    ).all()

    stats_df = pd.DataFrame(results, columns=[
        'player_id', 'name', 'points', 'rebounds', 'assists', 'steals', 'blocks', 'threes', 'turnovers', 'fg_pct', 'ft_pct'
    ])

    # Simple fantasy value as sum of categories (ignoring turnovers for now)
    stats_df['fantasy_value'] = (
        stats_df['points'] + stats_df['rebounds'] + stats_df['assists'] +
        stats_df['steals'] + stats_df['blocks'] + stats_df['threes'] +
        stats_df['fg_pct'] * 10 + stats_df['ft_pct'] * 10
    )

    return stats_df[['player_id', 'name', 'fantasy_value']]


def simulate_draft(player_pool: pd.DataFrame, strategy: str, roster_size: int = 13):
    if strategy == "adp":
        players_sorted = player_pool.sort_values("adp", ascending=True)
    elif strategy == "model":
        players_sorted = player_pool.sort_values("fantasy_value", ascending=False)
    else:
        raise ValueError("Invalid strategy: must be 'adp' or 'model'")

    drafted_team = players_sorted.head(roster_size)
    return drafted_team


# def evaluate_team(drafted_team: pd.DataFrame, actual_stats: pd.DataFrame):
#     merged = drafted_team.merge(actual_stats, on='player_id', how='left')
#     total_fantasy_value = merged['fantasy_value'].sum()
#     return total_fantasy_value


def plot_results(adp_score, model_score):
    labels = ['ADP Draft', 'Model Draft']
    scores = [adp_score, model_score]

    plt.bar(labels, scores)
    plt.title('Draft Simulation Results (2023-24 Season)')
    plt.ylabel('Total Fantasy Value (Sum of 9-Cat)')
    plt.show()


# --- Main Entry ---

def main():
    db_session = SessionLocal()

    print("📥 Loading data...")
    adp_data = load_adp_data()
    actual_stats = load_actual_season_stats(db_session)

    # Merge ADP with fantasy values BEFORE simulation
    adp_data = adp_data.merge(actual_stats[['player_id', 'fantasy_value']], on='player_id', how='left')

    print("\n🛠️ Simulating drafts...")
    adp_team = simulate_draft(adp_data, strategy="adp")
    model_team = simulate_draft(actual_stats, strategy="model")

    print("\n📈 Evaluating drafted teams...")
    adp_score = adp_team['fantasy_value'].sum()
    model_score = model_team['fantasy_value'].sum()

    print(f"\n🏀 ADP Draft Total Fantasy Value: {adp_score:.2f}")
    print(f"🤖 Model Draft Total Fantasy Value: {model_score:.2f}")

    print("\n📊 Plotting results...")
    plot_results(adp_score, model_score)


if __name__ == "__main__":
    main()

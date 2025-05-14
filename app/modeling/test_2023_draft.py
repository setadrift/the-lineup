"""
Test draft strategies using historical data and projections.
"""

import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Optional

from app.models.models import Player, PlayerStats
from app.utils.db import get_db
from app.utils.validation import validate_season_format
from app.utils.logging import setup_logger, log_execution_time
from app.config.constants import PACE_FACTORS, INJURY_RISK

# Set up logger
logger = setup_logger(__name__)

def load_adp_data() -> pd.DataFrame:
    """
    Load and process ADP data, mapping player names to IDs.
    
    Returns:
        pd.DataFrame: Processed ADP data
    """
    try:
        adp_path = "app/data/adp/2023_24_adp.csv"
        adp_df = pd.read_csv(adp_path)
        adp_df['clean_name'] = adp_df['Player'].apply(
            lambda x: ' '.join(reversed(x.split(', '))) if ', ' in x else x
        )
        
        with get_db() as session:
            players = session.query(Player.player_id, Player.name).all()
            player_map = {name: pid for pid, name in players}
            
            adp_df['player_id'] = adp_df['clean_name'].map(player_map)
            valid_players = adp_df.dropna(subset=['player_id'])
            
            if len(valid_players) < len(adp_df):
                logger.warning(
                    f"⚠️ Could not find player_ids for {len(adp_df) - len(valid_players)} players"
                )
                
            result = valid_players[['player_id', 'clean_name', 'Rank']].copy()
            result.columns = ['player_id', 'name', 'adp']
            
            logger.info(f"✅ Loaded ADP data for {len(result)} players")
            return result
            
    except Exception as e:
        logger.error(f"❌ Failed to load ADP data: {e}", exc_info=True)
        raise

def load_actual_season_stats(season: str = "2023-24") -> pd.DataFrame:
    """
    Load actual season stats and compute fantasy values.
    
    Args:
        season (str): Season in format '2023-24'
        
    Returns:
        pd.DataFrame: Player stats with fantasy values
        
    Raises:
        ValueError: If season format is invalid
    """
    if not validate_season_format(season):
        raise ValueError(f"Invalid season format: {season}. Expected format: YYYY-YY")
    
    with get_db() as session:
        results = session.query(
            PlayerStats.player_id,
            Player.name,
            Player.team,
            Player.position,
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
            PlayerStats.season == season
        ).all()

        stats_df = pd.DataFrame(results, columns=[
            'player_id', 'name', 'team', 'position',
            'points', 'rebounds', 'assists', 'steals',
            'blocks', 'threes', 'turnovers', 'fg_pct', 'ft_pct'
        ])

        # Calculate fantasy value
        stats_df['fantasy_value'] = (
            stats_df['points'] + stats_df['rebounds'] + stats_df['assists'] +
            stats_df['steals'] + stats_df['blocks'] + stats_df['threes'] +
            stats_df['fg_pct'] * 10 + stats_df['ft_pct'] * 10
        )

        # Apply pace and injury factors
        def apply_adjustments(row):
            pace = PACE_FACTORS.get(row['team'], 1.00)
            injury = INJURY_RISK.get(row['name'], 1.00)
            return row['fantasy_value'] * pace * injury

        stats_df['adjusted_projection'] = stats_df.apply(apply_adjustments, axis=1)
        
        logger.info(f"✅ Loaded season stats for {len(stats_df)} players")
        return stats_df[['player_id', 'name', 'position', 'fantasy_value', 'adjusted_projection']]

def simulate_draft(
    player_pool: pd.DataFrame,
    strategy: str,
    roster_size: int = 13
) -> pd.DataFrame:
    """
    Simulate a fantasy draft using specified strategy.
    
    Args:
        player_pool (pd.DataFrame): Available players
        strategy (str): Draft strategy ('adp', 'model', or 'adjusted_model')
        roster_size (int): Number of players to draft
        
    Returns:
        pd.DataFrame: Drafted team
        
    Raises:
        ValueError: If invalid strategy provided
    """
    valid_strategies = ['adp', 'model', 'adjusted_model']
    if strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy: {strategy}. Must be one of {valid_strategies}")
    
    # Sort players based on strategy
    if strategy == "adp":
        players_sorted = player_pool.sort_values("adp", ascending=True)
    elif strategy == "model":
        players_sorted = player_pool.sort_values("fantasy_value", ascending=False)
    else:  # adjusted_model
        players_sorted = player_pool.sort_values("adjusted_projection", ascending=False)

    drafted = []
    needs = {
        'G': 2,  # Guards
        'F': 2,  # Forwards
        'C': 1,  # Centers
        'G/F': 1,  # Guard/Forward flex
        'F/C': 1,  # Forward/Center flex
        'Bench': roster_size - 7  # Remaining bench spots
    }

    def fits_position(player_pos: str, need: str) -> bool:
        """Check if player fits position need."""
        if need == 'G':
            return 'Guard' in player_pos
        elif need == 'F':
            return 'Forward' in player_pos
        elif need == 'C':
            return 'Center' in player_pos
        elif need == 'G/F':
            return 'Guard' in player_pos or 'Forward' in player_pos
        elif need == 'F/C':
            return 'Forward' in player_pos or 'Center' in player_pos
        else:
            return True  # Bench can be any position

    # Draft players by position need
    for need, count in needs.items():
        for _ in range(count):
            for idx, player in players_sorted.iterrows():
                if player['player_id'] in [p['player_id'] for p in drafted]:
                    continue  # Already drafted
                
                if fits_position(player['position'], need):
                    drafted.append(player)
                    break

    drafted_team = pd.DataFrame(drafted)
    logger.info(f"✅ Drafted {len(drafted_team)} players using {strategy} strategy")
    return drafted_team

def plot_results(adp_score: float, model_score: float, adjusted_score: float):
    """
    Plot draft simulation results.
    
    Args:
        adp_score (float): Total fantasy value using ADP
        model_score (float): Total fantasy value using base model
        adjusted_score (float): Total fantasy value using adjusted model
    """
    labels = ['ADP Draft', 'Model Draft', 'Adjusted Model Draft']
    scores = [adp_score, model_score, adjusted_score]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, scores)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{height:.1f}',
            ha='center',
            va='bottom'
        )

    plt.title('Draft Simulation Results (2023-24 Season)')
    plt.ylabel('Total Fantasy Value (Sum of 9-Cat)')
    plt.grid(True, alpha=0.3)
    plt.show()

def main():
    """Run draft simulations and compare strategies."""
    try:
        import time
        start_time = time.time()
        
        logger.info("📥 Loading data...")
        adp_data = load_adp_data()
        actual_stats = load_actual_season_stats("2023-24")

        # Merge ADP data with actual stats
        adp_data = adp_data.merge(
            actual_stats[['player_id', 'position', 'fantasy_value', 'adjusted_projection']],
            on='player_id',
            how='left'
        )

        logger.info("\n🛠️ Simulating drafts...")
        adp_team = simulate_draft(adp_data, strategy="adp")
        model_team = simulate_draft(actual_stats, strategy="model")
        adjusted_team = simulate_draft(actual_stats, strategy="adjusted_model")

        logger.info("\n📈 Evaluating drafted teams...")
        adp_score = adp_team['fantasy_value'].sum()
        model_score = model_team['fantasy_value'].sum()
        adjusted_score = adjusted_team['adjusted_projection'].sum()

        logger.info(f"\n🏀 ADP Draft Total Fantasy Value: {adp_score:.2f}")
        logger.info(f"🤖 Model Draft Total Fantasy Value: {model_score:.2f}")
        logger.info(f"🚀 Adjusted Model Draft Total Fantasy Value: {adjusted_score:.2f}")

        logger.info("\n📊 Plotting results...")
        plot_results(adp_score, model_score, adjusted_score)
        
        log_execution_time(logger, start_time, "Draft simulation completed")

    except Exception as e:
        logger.error("❌ Draft simulation failed", exc_info=True)
        raise

if __name__ == "__main__":
    main()

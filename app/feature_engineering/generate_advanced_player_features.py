import sys
import os
import datetime
import pandas as pd
import numpy as np
from scipy.stats import zscore
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import PlayerStats, PlayerFeatures

def fetch_player_stats_with_advanced(session: Session, season: str) -> pd.DataFrame:
    """
    Fetch player stats including advanced metrics.
    
    Args:
        session: Database session
        season: NBA season (e.g., "2023-24")
        
    Returns:
        DataFrame with all player stats including advanced metrics
    """
    query = text("""
    SELECT 
        player_id, season, team, games_played, minutes_per_game,
        -- Basic stats
        points_per_game, rebounds_per_game, assists_per_game,
        steals_per_game, blocks_per_game, turnovers_per_game,
        fg_pct, ft_pct, three_pm,
        -- Advanced stats
        age, usage_rate, true_shooting_pct, effective_fg_pct,
        player_efficiency_rating,
        -- Per-36 stats
        points_per_36, rebounds_per_36, assists_per_36,
        steals_per_36, blocks_per_36, turnovers_per_36,
        -- Advanced percentages
        three_point_attempt_rate, free_throw_rate,
        offensive_rebound_pct, defensive_rebound_pct, total_rebound_pct,
        assist_pct, steal_pct, block_pct, turnover_pct
    FROM player_stats 
    WHERE season = :season
    """)
    
    result = session.execute(query, {"season": season})
    columns = result.keys()
    data = [dict(zip(columns, row)) for row in result.fetchall()]
    
    return pd.DataFrame(data)

def compute_advanced_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute enhanced z-scores including advanced stats.
    
    Args:
        df: Player stats DataFrame with advanced metrics
        
    Returns:
        DataFrame with comprehensive z-scores
    """
    # Filter for players with meaningful minutes (>= 15 MPG and >= 20 games)
    qualified_df = df[
        (df['minutes_per_game'] >= 15) & 
        (df['games_played'] >= 20)
    ].copy()
    
    if len(qualified_df) < 50:  # Fallback if too restrictive
        qualified_df = df[df['games_played'] >= 10].copy()
    
    print(f"Computing z-scores for {len(qualified_df)} qualified players")
    
    # Basic 9-cat z-scores (traditional fantasy categories)
    basic_stats = {
        "points_per_game": "z_points",
        "rebounds_per_game": "z_rebounds", 
        "assists_per_game": "z_assists",
        "steals_per_game": "z_steals",
        "blocks_per_game": "z_blocks",
        "turnovers_per_game": "z_turnovers",  # Inverted
        "fg_pct": "z_fg_pct",
        "ft_pct": "z_ft_pct",
        "three_pm": "z_three_pm"
    }
    
    # Advanced efficiency z-scores
    advanced_stats = {
        "usage_rate": "z_usage_rate",
        "true_shooting_pct": "z_true_shooting",
        "player_efficiency_rating": "z_per",
        "total_rebound_pct": "z_total_reb_pct",
        "assist_pct": "z_assist_pct",
        "steal_pct": "z_steal_pct",
        "block_pct": "z_block_pct",
        "turnover_pct": "z_turnover_pct"  # Inverted
    }
    
    # Per-36 z-scores (for comparing players with different minutes)
    per36_stats = {
        "points_per_36": "z_points_per_36",
        "rebounds_per_36": "z_rebounds_per_36",
        "assists_per_36": "z_assists_per_36", 
        "steals_per_36": "z_steals_per_36",
        "blocks_per_36": "z_blocks_per_36",
        "turnovers_per_36": "z_turnovers_per_36"  # Inverted
    }
    
    # Initialize result DataFrame
    z_df = pd.DataFrame()
    z_df["player_id"] = qualified_df["player_id"]
    z_df["season"] = qualified_df["season"]
    
    # Compute basic z-scores
    for raw_col, z_col in basic_stats.items():
        if raw_col in qualified_df.columns:
            values = qualified_df[raw_col].fillna(0)
            if raw_col == "turnovers_per_game":
                z_df[z_col] = -1 * zscore(values)  # Lower turnovers = better
            else:
                z_df[z_col] = zscore(values)
        else:
            z_df[z_col] = 0
    
    # Compute advanced z-scores
    for raw_col, z_col in advanced_stats.items():
        if raw_col in qualified_df.columns:
            values = qualified_df[raw_col].fillna(qualified_df[raw_col].median())
            if raw_col == "turnover_pct":
                z_df[z_col] = -1 * zscore(values)  # Lower turnover rate = better
            else:
                z_df[z_col] = zscore(values)
        else:
            z_df[z_col] = 0
    
    # Compute per-36 z-scores
    for raw_col, z_col in per36_stats.items():
        if raw_col in qualified_df.columns:
            values = qualified_df[raw_col].fillna(0)
            if raw_col == "turnovers_per_36":
                z_df[z_col] = -1 * zscore(values)  # Lower turnovers = better
            else:
                z_df[z_col] = zscore(values)
        else:
            z_df[z_col] = 0
    
    # Calculate composite scores
    
    # Traditional 9-cat total (for standard leagues)
    basic_z_cols = list(basic_stats.values())
    z_df["total_z_score"] = z_df[basic_z_cols].sum(axis=1)
    
    # Advanced efficiency score (for deeper analysis)
    advanced_z_cols = list(advanced_stats.values())
    z_df["advanced_z_score"] = z_df[advanced_z_cols].sum(axis=1)
    
    # Per-36 score (for upside evaluation)
    per36_z_cols = list(per36_stats.values())
    z_df["per36_z_score"] = z_df[per36_z_cols].sum(axis=1)
    
    # Composite fantasy score (weighted combination)
    z_df["composite_z_score"] = (
        z_df["total_z_score"] * 0.6 +      # 60% traditional stats
        z_df["advanced_z_score"] * 0.3 +   # 30% advanced efficiency
        z_df["per36_z_score"] * 0.1        # 10% per-36 upside
    )
    
    # Add age-adjusted scores for dynasty/keeper leagues
    if 'age' in qualified_df.columns:
        age_data = qualified_df.set_index('player_id')['age']
        z_df = z_df.set_index('player_id').join(age_data).reset_index()
        
        # Age adjustment factor (peak is around 27, decline after 30)
        z_df['age_factor'] = z_df['age'].apply(lambda x: 
            1.0 if pd.isna(x) else
            1.1 if x <= 25 else
            1.05 if x <= 27 else  
            1.0 if x <= 29 else
            0.95 if x <= 31 else
            0.9 if x <= 33 else
            0.85
        )
        
        z_df["age_adjusted_z_score"] = z_df["composite_z_score"] * z_df["age_factor"]
    else:
        z_df["age_adjusted_z_score"] = z_df["composite_z_score"]
    
    # Add timestamps
    now = datetime.datetime.utcnow()
    z_df["created_at"] = now
    z_df["updated_at"] = now
    
    print(f"✅ Computed enhanced z-scores for {len(z_df)} players")
    return z_df

def create_player_tiers(z_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create player tiers based on composite z-scores.
    
    Args:
        z_df: DataFrame with z-scores
        
    Returns:
        DataFrame with tier assignments
    """
    z_df = z_df.copy()
    
    # Define tier thresholds based on composite z-score
    def assign_tier(score):
        if score >= 8:
            return "Elite (Tier 1)"
        elif score >= 5:
            return "Star (Tier 2)" 
        elif score >= 2:
            return "Solid (Tier 3)"
        elif score >= 0:
            return "Decent (Tier 4)"
        elif score >= -2:
            return "Streamer (Tier 5)"
        else:
            return "Waiver (Tier 6)"
    
    z_df["tier"] = z_df["composite_z_score"].apply(assign_tier)
    
    # Add tier rankings within each tier
    z_df["tier_rank"] = z_df.groupby("tier")["composite_z_score"].rank(method="dense", ascending=False)
    
    return z_df

def save_advanced_player_features(z_df: pd.DataFrame, session: Session):
    """
    Save enhanced player features to database.
    
    Args:
        z_df: DataFrame with z-scores and features
        session: Database session
    """
    # Delete existing features for this season
    season = z_df["season"].iloc[0]
    session.query(PlayerFeatures).filter(PlayerFeatures.season == season).delete()
    
    # Convert DataFrame to PlayerFeatures objects
    features_list = []
    for _, row in z_df.iterrows():
        feature = PlayerFeatures(
            player_id=int(row["player_id"]),
            season=row["season"],
            # Basic z-scores
            z_points=float(row.get("z_points", 0)),
            z_rebounds=float(row.get("z_rebounds", 0)),
            z_assists=float(row.get("z_assists", 0)),
            z_steals=float(row.get("z_steals", 0)),
            z_blocks=float(row.get("z_blocks", 0)),
            z_turnovers=float(row.get("z_turnovers", 0)),
            z_fg_pct=float(row.get("z_fg_pct", 0)),
            z_ft_pct=float(row.get("z_ft_pct", 0)),
            z_three_pm=float(row.get("z_three_pm", 0)),
            total_z_score=float(row.get("total_z_score", 0)),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        features_list.append(feature)
    
    # Bulk insert
    session.add_all(features_list)
    session.commit()
    
    print(f"✅ Saved {len(features_list)} player features to database")

def generate_advanced_player_features(season: str = "2023-24"):
    """
    Main function to generate enhanced player features with advanced stats.
    
    Args:
        season: NBA season to process
    """
    print(f"🚀 Generating advanced player features for {season}...")
    
    session = SessionLocal()
    try:
        # Fetch player stats with advanced metrics
        print("📊 Fetching player stats with advanced metrics...")
        df = fetch_player_stats_with_advanced(session, season)
        
        if df.empty:
            print(f"❌ No player stats found for {season}")
            return
        
        print(f"📈 Processing {len(df)} players...")
        
        # Compute enhanced z-scores
        z_df = compute_advanced_z_scores(df)
        
        # Create player tiers
        z_df = create_player_tiers(z_df)
        
        # Save to database
        save_advanced_player_features(z_df, session)
        
        # Print summary
        print(f"\n📊 Advanced Features Summary for {season}:")
        print(f"Total Players: {len(z_df)}")
        print(f"Tier Distribution:")
        tier_counts = z_df["tier"].value_counts().sort_index()
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count} players")
        
        print(f"\nTop 10 Players by Composite Z-Score:")
        top_players = z_df.nlargest(10, "composite_z_score")[
            ["player_id", "composite_z_score", "total_z_score", "advanced_z_score", "tier"]
        ]
        print(top_players.to_string(index=False))
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error generating advanced features: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate advanced player features")
    parser.add_argument("--season", default="2023-24", help="NBA season (e.g., 2023-24)")
    parser.add_argument("--all-seasons", action="store_true", help="Process all available seasons")
    
    args = parser.parse_args()
    
    if args.all_seasons:
        seasons = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
        for season in seasons:
            try:
                generate_advanced_player_features(season)
                print(f"✅ Completed {season}")
            except Exception as e:
                print(f"❌ Failed {season}: {e}")
    else:
        generate_advanced_player_features(args.season) 
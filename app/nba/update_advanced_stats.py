import sys
import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import update, text
from datetime import datetime

# Set project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.models.models import PlayerStats
from app.nba.fetch_advanced_stats import fetch_all_advanced_stats, merge_advanced_stats

def update_player_stats_with_advanced(season: str = "2023-24"):
    """
    Update existing player_stats records with advanced stats data.
    
    Args:
        season: NBA season to update (e.g., "2023-24")
    """
    print(f"🔄 Starting advanced stats update for {season}...")
    
    # Fetch all advanced stats
    try:
        all_stats = fetch_all_advanced_stats(season)
        merged_stats = merge_advanced_stats(all_stats)
        
        if merged_stats.empty:
            print("❌ No advanced stats data retrieved")
            return
            
        print(f"📊 Retrieved advanced stats for {len(merged_stats)} players")
        
    except Exception as e:
        print(f"❌ Error fetching advanced stats: {e}")
        return
    
    # Update database
    db = SessionLocal()
    try:
        updated_count = 0
        
        for _, row in merged_stats.iterrows():
            player_id = row['player_id']
            
            # Prepare update data - only include non-null values
            update_data = {}
            
            # Advanced stats columns to update
            advanced_columns = {
                'age': 'age',
                'usage_rate': 'usage_rate',
                'true_shooting_pct': 'true_shooting_pct',
                'effective_fg_pct': 'effective_fg_pct',
                'player_efficiency_rating': 'player_efficiency_rating',
                'points_per_36': 'points_per_36',
                'rebounds_per_36': 'rebounds_per_36',
                'assists_per_36': 'assists_per_36',
                'steals_per_36': 'steals_per_36',
                'blocks_per_36': 'blocks_per_36',
                'turnovers_per_36': 'turnovers_per_36',
                'three_point_attempt_rate': 'three_point_attempt_rate',
                'free_throw_rate': 'free_throw_rate',
                'offensive_rebound_pct': 'offensive_rebound_pct',
                'defensive_rebound_pct': 'defensive_rebound_pct',
                'total_rebound_pct': 'total_rebound_pct',
                'assist_pct': 'assist_pct',
                'steal_pct': 'steal_pct',
                'block_pct': 'block_pct',
                'turnover_pct': 'turnover_pct'
            }
            
            # Add values that are not null/NaN
            for df_col, db_col in advanced_columns.items():
                if df_col in row and pd.notna(row[df_col]):
                    update_data[db_col] = float(row[df_col])
            
            # Always update the timestamp
            update_data['last_updated'] = datetime.utcnow()
            
            if update_data:
                # Update the player's stats
                result = db.execute(
                    update(PlayerStats)
                    .where(PlayerStats.player_id == player_id)
                    .where(PlayerStats.season == season)
                    .values(**update_data)
                )
                
                if result.rowcount > 0:
                    updated_count += 1
                    if updated_count % 50 == 0:
                        print(f"📈 Updated {updated_count} players...")
        
        # Commit all updates
        db.commit()
        print(f"✅ Successfully updated {updated_count} player records with advanced stats")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating database: {e}")
        raise
    finally:
        db.close()

def get_advanced_stats_summary(season: str = "2023-24"):
    """
    Get a summary of advanced stats coverage in the database.
    
    Args:
        season: NBA season to check
    """
    db = SessionLocal()
    try:
        # Query to check advanced stats coverage
        query = text("""
        SELECT 
            COUNT(*) as total_players,
            COUNT(usage_rate) as usage_rate_count,
            COUNT(true_shooting_pct) as true_shooting_count,
            COUNT(player_efficiency_rating) as per_count,
            COUNT(points_per_36) as per36_count,
            COUNT(offensive_rebound_pct) as rebound_pct_count
        FROM player_stats 
        WHERE season = :season
        """)
        
        result = db.execute(query, {"season": season}).fetchone()
        
        print(f"\n📊 Advanced Stats Coverage for {season}:")
        print(f"Total Players: {result[0]}")
        print(f"Usage Rate: {result[1]} ({result[1]/result[0]*100:.1f}%)")
        print(f"True Shooting %: {result[2]} ({result[2]/result[0]*100:.1f}%)")
        print(f"Player Efficiency Rating: {result[3]} ({result[3]/result[0]*100:.1f}%)")
        print(f"Per-36 Stats: {result[4]} ({result[4]/result[0]*100:.1f}%)")
        print(f"Rebounding %: {result[5]} ({result[5]/result[0]*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
    finally:
        db.close()

def test_advanced_stats_fetch():
    """
    Test function to verify advanced stats fetching works.
    """
    print("🧪 Testing advanced stats fetch...")
    
    try:
        # Test fetching a small sample
        all_stats = fetch_all_advanced_stats("2023-24")
        
        print(f"📊 Fetched stats types: {list(all_stats.keys())}")
        
        for stat_type, df in all_stats.items():
            print(f"  {stat_type}: {len(df)} players, {len(df.columns)} columns")
            if not df.empty:
                print(f"    Sample columns: {list(df.columns)[:5]}")
        
        # Test merging
        merged = merge_advanced_stats(all_stats)
        print(f"📊 Merged stats: {len(merged)} players, {len(merged.columns)} columns")
        
        if not merged.empty:
            print(f"📊 Sample merged columns: {list(merged.columns)[:10]}")
            print(f"📊 Sample data for first player:")
            print(merged.iloc[0].to_dict())
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update player stats with advanced metrics")
    parser.add_argument("--season", default="2023-24", help="NBA season (e.g., 2023-24)")
    parser.add_argument("--test", action="store_true", help="Run test mode only")
    parser.add_argument("--summary", action="store_true", help="Show coverage summary only")
    
    args = parser.parse_args()
    
    if args.test:
        test_advanced_stats_fetch()
    elif args.summary:
        get_advanced_stats_summary(args.season)
    else:
        update_player_stats_with_advanced(args.season)
        get_advanced_stats_summary(args.season) 
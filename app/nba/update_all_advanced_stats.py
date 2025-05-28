import sys
import os
from typing import List

# Set project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.nba.update_advanced_stats import (
    update_player_stats_with_advanced, 
    get_advanced_stats_summary,
    test_advanced_stats_fetch
)

# All seasons with data
SEASONS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

def update_all_seasons_advanced_stats(seasons: List[str] = None):
    """
    Update advanced stats for all specified seasons.
    
    Args:
        seasons: List of seasons to update. If None, uses all available seasons.
    """
    if seasons is None:
        seasons = SEASONS
    
    print(f"🚀 Starting advanced stats update for {len(seasons)} seasons...")
    print(f"📅 Seasons: {', '.join(seasons)}")
    
    successful_updates = []
    failed_updates = []
    
    for i, season in enumerate(seasons, 1):
        print(f"\n{'='*60}")
        print(f"📊 Processing Season {i}/{len(seasons)}: {season}")
        print(f"{'='*60}")
        
        try:
            # Update advanced stats for this season
            update_player_stats_with_advanced(season)
            successful_updates.append(season)
            print(f"✅ Successfully updated {season}")
            
        except Exception as e:
            print(f"❌ Failed to update {season}: {e}")
            failed_updates.append((season, str(e)))
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📈 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful updates: {len(successful_updates)}")
    for season in successful_updates:
        print(f"   - {season}")
    
    if failed_updates:
        print(f"\n❌ Failed updates: {len(failed_updates)}")
        for season, error in failed_updates:
            print(f"   - {season}: {error}")
    
    print(f"\n🎯 Overall success rate: {len(successful_updates)}/{len(seasons)} ({len(successful_updates)/len(seasons)*100:.1f}%)")

def get_all_seasons_summary(seasons: List[str] = None):
    """
    Get advanced stats summary for all seasons.
    
    Args:
        seasons: List of seasons to check. If None, uses all available seasons.
    """
    if seasons is None:
        seasons = SEASONS
    
    print(f"📊 Advanced Stats Coverage Summary")
    print(f"{'='*60}")
    
    for season in seasons:
        try:
            get_advanced_stats_summary(season)
        except Exception as e:
            print(f"❌ Error getting summary for {season}: {e}")

def verify_seasons_data(seasons: List[str] = None):
    """
    Verify that we have basic player stats data for all seasons before updating advanced stats.
    
    Args:
        seasons: List of seasons to verify. If None, uses all available seasons.
    """
    if seasons is None:
        seasons = SEASONS
    
    print(f"🔍 Verifying basic stats data for {len(seasons)} seasons...")
    
    from app.db.connection import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        for season in seasons:
            count = db.execute(
                text("SELECT COUNT(*) FROM player_stats WHERE season = :season"), 
                {"season": season}
            ).fetchone()[0]
            
            if count > 0:
                print(f"✅ {season}: {count} players")
            else:
                print(f"❌ {season}: No data found")
                
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update advanced stats for all seasons")
    parser.add_argument("--seasons", nargs="+", default=SEASONS, help="Specific seasons to update")
    parser.add_argument("--verify", action="store_true", help="Verify basic stats data exists")
    parser.add_argument("--summary", action="store_true", help="Show coverage summary for all seasons")
    parser.add_argument("--test", action="store_true", help="Run test mode only")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Testing advanced stats fetch for current season...")
        test_advanced_stats_fetch()
    elif args.verify:
        verify_seasons_data(args.seasons)
    elif args.summary:
        get_all_seasons_summary(args.seasons)
    else:
        # First verify we have data
        print("🔍 Step 1: Verifying basic stats data...")
        verify_seasons_data(args.seasons)
        
        input("\n⏸️  Press Enter to continue with advanced stats update, or Ctrl+C to cancel...")
        
        # Then update advanced stats
        print("\n🚀 Step 2: Updating advanced stats...")
        update_all_seasons_advanced_stats(args.seasons)
        
        # Finally show summary
        print("\n📊 Step 3: Final coverage summary...")
        get_all_seasons_summary(args.seasons) 
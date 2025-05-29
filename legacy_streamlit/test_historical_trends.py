#!/usr/bin/env python3
"""
Test script for Historical Trends functionality
"""

import sys
import os
import asyncio
import requests
from sqlalchemy.orm import Session

# Set up project path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app.db.connection import SessionLocal
from app.services.historical_stats_service import HistoricalStatsService
from app.models.models import Player, PlayerStats

def test_database_connection():
    """Test database connection and basic queries."""
    print("🔍 Testing database connection...")
    
    try:
        db = SessionLocal()
        
        # Test basic connection
        player_count = db.query(Player).count()
        stats_count = db.query(PlayerStats).count()
        
        print(f"✅ Database connected successfully")
        print(f"   - Players in database: {player_count}")
        print(f"   - Player stats records: {stats_count}")
        
        # Get a sample player for testing
        sample_player = db.query(Player).first()
        if sample_player:
            print(f"   - Sample player: {sample_player.name} (ID: {sample_player.player_id})")
            return sample_player.player_id, sample_player.name
        else:
            print("⚠️  No players found in database")
            return None, None
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None, None
    finally:
        db.close()

def test_historical_stats_service(player_id: int, player_name: str):
    """Test the HistoricalStatsService functionality."""
    print(f"\n📊 Testing HistoricalStatsService for {player_name} (ID: {player_id})...")
    
    try:
        db = SessionLocal()
        service = HistoricalStatsService(db)
        
        # Test getting historical stats
        print("   - Fetching historical stats...")
        historical_stats = service.get_player_historical_stats(player_id, seasons_back=3)
        print(f"     Found {len(historical_stats)} seasons of data")
        
        if historical_stats:
            for stat in historical_stats:
                print(f"     - {stat['season']}: {stat['points_per_game']:.1f} PPG, {stat['rebounds_per_game']:.1f} RPG")
        
        # Test sparkline generation
        print("   - Generating sparklines...")
        sparklines = service.get_all_sparklines_for_player(player_id, seasons_back=3)
        
        for stat_name, sparkline_data in sparklines.items():
            values = sparkline_data.get('values', [])
            trend = sparkline_data.get('trend', 'unknown')
            if values:
                print(f"     - {stat_name}: {len(values)} seasons, trend: {trend}")
        
        # Test complete player trends
        print("   - Getting complete player trends...")
        complete_data = service.get_player_with_trends(player_id, seasons_back=3)
        
        if complete_data:
            seasons_analyzed = complete_data.get('seasons_analyzed', 0)
            print(f"     Complete data retrieved: {seasons_analyzed} seasons analyzed")
            print("✅ HistoricalStatsService working correctly")
        else:
            print("⚠️  No complete data returned")
            
    except Exception as e:
        print(f"❌ HistoricalStatsService test failed: {e}")
    finally:
        db.close()

def test_api_endpoints():
    """Test the FastAPI endpoints."""
    print("\n🌐 Testing API endpoints...")
    
    try:
        # Test if server is running
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            
            # Test supported stats endpoint
            response = requests.get("http://localhost:8000/api/historical/supported-stats")
            if response.status_code == 200:
                data = response.json()
                supported_stats = data.get('supported_stats', [])
                print(f"   - Supported stats endpoint working: {len(supported_stats)} stats")
            else:
                print(f"⚠️  Supported stats endpoint returned: {response.status_code}")
            
            # Test with a sample player (if we have one)
            db = SessionLocal()
            sample_player = db.query(Player).first()
            db.close()
            
            if sample_player:
                player_id = sample_player.player_id
                
                # Test player trends endpoint
                response = requests.get(f"http://localhost:8000/api/historical/player/{player_id}/trends")
                if response.status_code == 200:
                    print(f"   - Player trends endpoint working for player {player_id}")
                elif response.status_code == 404:
                    print(f"   - Player {player_id} not found (expected if no historical data)")
                else:
                    print(f"⚠️  Player trends endpoint returned: {response.status_code}")
                
                # Test sparklines endpoint
                response = requests.get(f"http://localhost:8000/api/historical/player/{player_id}/sparklines")
                if response.status_code == 200:
                    print(f"   - Sparklines endpoint working for player {player_id}")
                else:
                    print(f"⚠️  Sparklines endpoint returned: {response.status_code}")
        else:
            print(f"❌ API server not responding: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Please start it with:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ API test failed: {e}")

def main():
    """Main test function."""
    print("🏀 The Lineup - Historical Trends Test Suite")
    print("=" * 50)
    
    # Test database connection
    player_id, player_name = test_database_connection()
    
    # Test service functionality
    if player_id and player_name:
        test_historical_stats_service(player_id, player_name)
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("   - Database connection: Check console output above")
    print("   - HistoricalStatsService: Check console output above")
    print("   - API endpoints: Check console output above")
    print("\n💡 To run the demo:")
    print("   streamlit run app/frontend/streamlit/pages/historical_trends_demo.py")

if __name__ == "__main__":
    main() 
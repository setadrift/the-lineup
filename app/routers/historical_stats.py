import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

# Set up project path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import get_db
from app.services.historical_stats_service import HistoricalStatsService

router = APIRouter(prefix="/api/historical", tags=["historical-stats"])

@router.get("/player/{player_id}/trends")
async def get_player_trends(
    player_id: int,
    seasons_back: int = Query(default=3, ge=1, le=10, description="Number of seasons to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete player information with historical stat trends and sparklines.
    
    Args:
        player_id: The player's ID
        seasons_back: Number of seasons to include (1-10, default 3)
        db: Database session
        
    Returns:
        Player info with historical stats and sparkline data
    """
    service = HistoricalStatsService(db)
    
    try:
        result = service.get_player_with_trends(player_id, seasons_back)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found")
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching player trends: {str(e)}")

@router.get("/player/{player_id}/sparkline/{stat_name}")
async def get_stat_sparkline(
    player_id: int,
    stat_name: str,
    seasons_back: int = Query(default=3, ge=1, le=10, description="Number of seasons to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sparkline data for a specific stat for a player.
    
    Args:
        player_id: The player's ID
        stat_name: Name of the stat (e.g., 'points_per_game')
        seasons_back: Number of seasons to include (1-10, default 3)
        db: Database session
        
    Returns:
        Sparkline data for the specified stat
    """
    service = HistoricalStatsService(db)
    
    try:
        result = service.generate_sparkline_data(player_id, stat_name, seasons_back)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sparkline: {str(e)}")

@router.get("/player/{player_id}/sparklines")
async def get_all_sparklines(
    player_id: int,
    seasons_back: int = Query(default=3, ge=1, le=10, description="Number of seasons to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Dict[str, Any]]:
    """
    Get sparkline data for all key stats for a player.
    
    Args:
        player_id: The player's ID
        seasons_back: Number of seasons to include (1-10, default 3)
        db: Database session
        
    Returns:
        Dictionary mapping stat names to sparkline data
    """
    service = HistoricalStatsService(db)
    
    try:
        result = service.get_all_sparklines_for_player(player_id, seasons_back)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sparklines: {str(e)}")

@router.get("/player/{player_id}/historical-stats")
async def get_historical_stats(
    player_id: int,
    seasons_back: int = Query(default=3, ge=1, le=10, description="Number of seasons to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get raw historical stats for a player across multiple seasons.
    
    Args:
        player_id: The player's ID
        seasons_back: Number of seasons to include (1-10, default 3)
        db: Database session
        
    Returns:
        List of season stats and metadata
    """
    service = HistoricalStatsService(db)
    
    try:
        historical_stats = service.get_player_historical_stats(player_id, seasons_back)
        
        return {
            "player_id": player_id,
            "seasons_analyzed": len(historical_stats),
            "historical_stats": historical_stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical stats: {str(e)}")

@router.get("/supported-stats")
async def get_supported_stats() -> Dict[str, Any]:
    """
    Get list of supported stats for sparkline generation.
    
    Returns:
        List of supported stat names and descriptions
    """
    stat_descriptions = {
        'points_per_game': 'Points per game',
        'rebounds_per_game': 'Rebounds per game',
        'assists_per_game': 'Assists per game',
        'steals_per_game': 'Steals per game',
        'blocks_per_game': 'Blocks per game',
        'turnovers_per_game': 'Turnovers per game',
        'fg_pct': 'Field goal percentage',
        'ft_pct': 'Free throw percentage',
        'three_pm': '3-pointers made per game'
    }
    
    return {
        "supported_stats": HistoricalStatsService.KEY_STATS,
        "descriptions": stat_descriptions
    } 
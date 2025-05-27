import sys
import os
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Set up project path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.db.connection import get_db
from app.models.models import PlayerStats, Player

class HistoricalStatsService:
    """Service for handling historical player statistics and trend analysis."""
    
    # Key stats for sparklines (9-cat fantasy basketball)
    KEY_STATS = [
        'points_per_game',
        'rebounds_per_game', 
        'assists_per_game',
        'steals_per_game',
        'blocks_per_game',
        'turnovers_per_game',
        'fg_pct',
        'ft_pct',
        'three_pm'
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_player_historical_stats(self, player_id: int, seasons_back: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch historical stats for a player across multiple seasons.
        
        Args:
            player_id: The player's ID
            seasons_back: Number of seasons to look back (default 3)
            
        Returns:
            List of dictionaries containing season stats
        """
        # Get the most recent seasons available for this player
        historical_stats = (
            self.db.query(PlayerStats)
            .filter(PlayerStats.player_id == player_id)
            .order_by(desc(PlayerStats.season))
            .limit(seasons_back)
            .all()
        )
        
        return [
            {
                'season': stat.season,
                'games_played': stat.games_played,
                'minutes_per_game': stat.minutes_per_game,
                'points_per_game': stat.points_per_game,
                'rebounds_per_game': stat.rebounds_per_game,
                'assists_per_game': stat.assists_per_game,
                'steals_per_game': stat.steals_per_game,
                'blocks_per_game': stat.blocks_per_game,
                'turnovers_per_game': stat.turnovers_per_game,
                'fg_pct': stat.fg_pct,
                'ft_pct': stat.ft_pct,
                'three_pm': stat.three_pm,
                'team': stat.team
            }
            for stat in reversed(historical_stats)  # Reverse to get chronological order
        ]
    
    def generate_sparkline_data(self, player_id: int, stat_name: str, seasons_back: int = 3) -> Dict[str, Any]:
        """
        Generate sparkline data for a specific stat across seasons.
        
        Args:
            player_id: The player's ID
            stat_name: Name of the stat (e.g., 'points_per_game')
            seasons_back: Number of seasons to include
            
        Returns:
            Dictionary with sparkline data and metadata
        """
        if stat_name not in self.KEY_STATS:
            raise ValueError(f"Stat '{stat_name}' not supported. Must be one of: {self.KEY_STATS}")
        
        historical_data = self.get_player_historical_stats(player_id, seasons_back)
        
        if not historical_data:
            return {
                'stat_name': stat_name,
                'values': [],
                'seasons': [],
                'trend': 'no_data',
                'min_value': None,
                'max_value': None,
                'latest_value': None,
                'change_from_previous': None
            }
        
        # Extract values and seasons
        values = []
        seasons = []
        
        for season_data in historical_data:
            value = season_data.get(stat_name)
            if value is not None:
                values.append(float(value))
                seasons.append(season_data['season'])
        
        if not values:
            return {
                'stat_name': stat_name,
                'values': [],
                'seasons': [],
                'trend': 'no_data',
                'min_value': None,
                'max_value': None,
                'latest_value': None,
                'change_from_previous': None
            }
        
        # Calculate trend
        trend = self._calculate_trend(values)
        
        # Calculate change from previous season
        change_from_previous = None
        if len(values) >= 2:
            change_from_previous = values[-1] - values[-2]
        
        return {
            'stat_name': stat_name,
            'values': values,
            'seasons': seasons,
            'trend': trend,
            'min_value': min(values),
            'max_value': max(values),
            'latest_value': values[-1] if values else None,
            'change_from_previous': change_from_previous,
            'percent_change': (change_from_previous / values[-2] * 100) if change_from_previous and len(values) >= 2 and values[-2] != 0 else None
        }
    
    def get_all_sparklines_for_player(self, player_id: int, seasons_back: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        Generate sparkline data for all key stats for a player.
        
        Args:
            player_id: The player's ID
            seasons_back: Number of seasons to include
            
        Returns:
            Dictionary mapping stat names to sparkline data
        """
        sparklines = {}
        
        for stat_name in self.KEY_STATS:
            sparklines[stat_name] = self.generate_sparkline_data(player_id, stat_name, seasons_back)
        
        return sparklines
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate the overall trend direction for a series of values.
        
        Args:
            values: List of numeric values in chronological order
            
        Returns:
            Trend direction: 'increasing', 'decreasing', 'stable', or 'volatile'
        """
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        # Calculate coefficient of variation to detect volatility
        std_dev = (sum((v - y_mean) ** 2 for v in values) / n) ** 0.5
        cv = std_dev / y_mean if y_mean != 0 else 0
        
        # Thresholds for trend classification
        slope_threshold = 0.1 * y_mean  # 10% of mean value
        volatility_threshold = 0.3  # 30% coefficient of variation
        
        if cv > volatility_threshold:
            return 'volatile'
        elif slope > slope_threshold:
            return 'increasing'
        elif slope < -slope_threshold:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_player_with_trends(self, player_id: int, seasons_back: int = 3) -> Dict[str, Any]:
        """
        Get complete player information including historical trends.
        
        Args:
            player_id: The player's ID
            seasons_back: Number of seasons to include in trends
            
        Returns:
            Dictionary with player info and all sparkline data
        """
        # Get basic player info
        player = self.db.query(Player).filter(Player.player_id == player_id).first()
        
        if not player:
            return None
        
        # Get historical stats
        historical_stats = self.get_player_historical_stats(player_id, seasons_back)
        
        # Get all sparklines
        sparklines = self.get_all_sparklines_for_player(player_id, seasons_back)
        
        return {
            'player_info': {
                'player_id': player.player_id,
                'name': player.name,
                'team': player.team,
                'position': player.position,
                'status': player.status,
                'bbm_rank': player.bbm_rank,
                'bbm_value': player.bbm_value,
                'adp': player.adp
            },
            'historical_stats': historical_stats,
            'sparklines': sparklines,
            'seasons_analyzed': len(historical_stats)
        } 
"""
Data validation utility functions.
"""

from typing import Union, List, Dict, Any
import pandas as pd
import numpy as np

def validate_season_format(season: str) -> bool:
    """
    Validate season string format (e.g., '2023-24').
    
    Args:
        season (str): Season string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not isinstance(season, str):
            return False
            
        if len(season) != 7:  # YYYY-YY format
            return False
            
        year1, year2 = season.split('-')
        if len(year1) != 4 or len(year2) != 2:
            return False
            
        if not (year1.isdigit() and year2.isdigit()):
            return False
            
        if int(year2) != (int(year1) + 1) % 100:
            return False
            
        return True
        
    except:
        return False

def validate_player_stats(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Validate player statistics DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing player stats
        
    Returns:
        Dict[str, List[str]]: Dictionary of validation errors by column
    """
    errors = {}
    
    # Required columns
    required_cols = [
        'player_id', 'season', 'team',
        'games_played', 'minutes_per_game',
        'points_per_game', 'rebounds_per_game',
        'assists_per_game', 'steals_per_game',
        'blocks_per_game', 'turnovers_per_game',
        'fg_pct', 'ft_pct', 'three_pm'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors['missing_columns'] = missing_cols
    
    # Data type validation
    if 'player_id' in df.columns and not pd.to_numeric(df['player_id'], errors='coerce').notna().all():
        errors['player_id'] = ['Contains non-numeric values']
    
    # Range validation for percentages
    for col in ['fg_pct', 'ft_pct']:
        if col in df.columns:
            invalid_pct = df[df[col].notna() & ((df[col] < 0) | (df[col] > 1))][col]
            if not invalid_pct.empty:
                errors[col] = [f'Values outside valid range (0-1): {list(invalid_pct.index)}']
    
    # Non-negative validation for game stats
    game_stats = ['games_played', 'minutes_per_game', 'points_per_game', 
                 'rebounds_per_game', 'assists_per_game', 'steals_per_game',
                 'blocks_per_game', 'turnovers_per_game', 'three_pm']
                 
    for col in game_stats:
        if col in df.columns:
            invalid_stats = df[df[col].notna() & (df[col] < 0)][col]
            if not invalid_stats.empty:
                errors[col] = [f'Negative values found: {list(invalid_stats.index)}']
    
    return errors

def validate_numeric_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    allow_none: bool = False
) -> bool:
    """
    Validate if a numeric value is within a specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_none: Whether None/null values are allowed
        
    Returns:
        bool: True if valid, False otherwise
    """
    if value is None:
        return allow_none
        
    try:
        num_val = float(value)
        return min_val <= num_val <= max_val
    except (TypeError, ValueError):
        return False 
"""
The Lineup - Database Utilities
Centralized database operations for the draft assistant
"""

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from typing import List, Optional


def get_database_engine():
    """
    Get database engine with connection pooling.
    
    Returns:
        SQLAlchemy engine instance
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        st.error("Database URL not found in environment variables")
        st.stop()
    
    return create_engine(DATABASE_URL)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_player_pool(season: str) -> pd.DataFrame:
    """
    Get the complete player pool with z-scores and ADP data.
    
    Args:
        season: NBA season (e.g., '2023-24')
        
    Returns:
        DataFrame with player pool data
    """
    engine = get_database_engine()
    
    query = """
    SELECT *
    FROM (
        SELECT DISTINCT ON (p.player_id)
            p.player_id,
            p.name,
            COALESCE(ps.team, p.team) as team,
            p.position,
            pf.total_z_score,
            pf.z_points,
            pf.z_rebounds,
            pf.z_assists,
            pf.z_steals,
            pf.z_blocks,
            pf.z_turnovers,
            pf.z_fg_pct,
            pf.z_ft_pct,
            pf.z_three_pm,
            psi.adp,
            p.injury_notes
        FROM players p
        JOIN player_features pf ON p.player_id = pf.player_id AND pf.season = %s
        LEFT JOIN player_stats ps ON p.player_id = ps.player_id AND ps.season = %s
        LEFT JOIN player_season_info psi ON p.player_id = psi.player_id AND psi.season = pf.season
        ORDER BY p.player_id, pf.total_z_score DESC
    ) sub
    ORDER BY total_z_score DESC
    """
    
    try:
        df = pd.read_sql(query, engine, params=(season, season))
        return df.rename(columns={
            'name': 'name',
            'team': 'team', 
            'position': 'position',
            'total_z_score': 'total_z_score',
            'z_points': 'z_points',
            'z_rebounds': 'z_rebounds',
            'z_assists': 'z_assists',
            'z_steals': 'z_steals',
            'z_blocks': 'z_blocks',
            'z_turnovers': 'z_turnovers',
            'z_fg_pct': 'z_fg_pct',
            'z_ft_pct': 'z_ft_pct',
            'z_three_pm': 'z_three_pm',
            'adp': 'adp',
            'injury_notes': 'injury_notes'
        })
    except Exception as e:
        st.error(f"Error loading player pool: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_detailed_player_stats(player_ids: List[str], season: str) -> pd.DataFrame:
    """
    Get detailed stats for specific players.
    
    Args:
        player_ids: List of player IDs
        season: NBA season
        
    Returns:
        DataFrame with detailed player statistics
    """
    if not player_ids:
        return pd.DataFrame()
    
    engine = get_database_engine()
    
    query = """
    SELECT DISTINCT ON (ps.player_id)
        ps.player_id,
        ps.points_per_game,
        ps.rebounds_per_game,
        ps.assists_per_game,
        ps.steals_per_game,
        ps.blocks_per_game,
        ps.turnovers_per_game,
        ps.fg_pct,
        ps.ft_pct,
        ps.three_pm,
        ps.games_played,
        pf.z_points,
        pf.z_rebounds,
        pf.z_assists,
        pf.z_steals,
        pf.z_blocks,
        pf.z_turnovers,
        pf.z_fg_pct,
        pf.z_ft_pct,
        pf.z_three_pm
    FROM player_stats ps
    JOIN player_features pf ON ps.player_id = pf.player_id AND ps.season = pf.season
    WHERE ps.season = %s AND ps.player_id = ANY(%s)
    ORDER BY ps.player_id
    """
    
    try:
        return pd.read_sql(query, engine, params=(season, player_ids))
    except Exception as e:
        st.error(f"Error loading detailed stats: {e}")
        return pd.DataFrame()


def get_player_by_ids(player_ids: List[str], player_pool_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get players from the pool by their IDs.
    
    Args:
        player_ids: List of player IDs
        player_pool_df: Full player pool DataFrame
        
    Returns:
        DataFrame with selected players
    """
    if not player_ids:
        return pd.DataFrame()
    
    return player_pool_df[player_pool_df["player_id"].isin(player_ids)]


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_seasons() -> List[str]:
    """
    Get list of available seasons from the database.
    
    Returns:
        List of available seasons
    """
    engine = get_database_engine()
    
    query = """
    SELECT DISTINCT season 
    FROM player_features 
    ORDER BY season DESC
    """
    
    try:
        result = pd.read_sql(query, engine)
        return result['season'].tolist()
    except Exception as e:
        st.error(f"Error loading seasons: {e}")
        return ["2023-24"]  # Fallback


def validate_database_connection() -> bool:
    """
    Validate that the database connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        engine = get_database_engine()
        # Simple query to test connection
        pd.read_sql("SELECT 1", engine)
        return True
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return False 
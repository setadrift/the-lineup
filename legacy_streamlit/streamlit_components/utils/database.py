"""
The Lineup - Database Utilities
Centralized database operations for the draft assistant
"""

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from st_supabase_connection import SupabaseConnection
from typing import List, Optional


@st.cache_resource
def get_database_engine():
    """
    Get database engine using Streamlit's connection.
    
    Returns:
        SQLAlchemy engine instance
    """
    conn = st.connection("supabase", type=SupabaseConnection)
    return conn.engine


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_player_pool(season: str) -> pd.DataFrame:
    """
    Get the complete player pool with enhanced z-scores and advanced stats.
    
    Args:
        season: NBA season (e.g., "2023-24")
        
    Returns:
        DataFrame with player pool including advanced metrics
    """
    engine = get_database_engine()
    
    query = """
    SELECT DISTINCT ON (pf.player_id)
        pf.player_id,
        p.name,
        p.position,
        ps.team,
        ps.age,
        ps.games_played,
        ps.minutes_per_game,
        -- Basic stats
        ps.points_per_game,
        ps.rebounds_per_game,
        ps.assists_per_game,
        ps.steals_per_game,
        ps.blocks_per_game,
        ps.turnovers_per_game,
        ps.fg_pct,
        ps.ft_pct,
        ps.three_pm,
        -- Advanced stats
        ps.usage_rate,
        ps.true_shooting_pct,
        ps.player_efficiency_rating,
        ps.points_per_36,
        ps.rebounds_per_36,
        ps.assists_per_36,
        -- Traditional z-scores
        pf.z_points,
        pf.z_rebounds,
        pf.z_assists,
        pf.z_steals,
        pf.z_blocks,
        pf.z_turnovers,
        pf.z_fg_pct,
        pf.z_ft_pct,
        pf.z_three_pm,
        pf.total_z_score,
        -- ADP and injury info
        psi.adp,
        psi.injury_notes
    FROM player_features pf
    JOIN players p ON pf.player_id = p.player_id
    JOIN player_stats ps ON pf.player_id = ps.player_id AND pf.season = ps.season
    LEFT JOIN player_season_info psi ON pf.player_id = psi.player_id AND pf.season = psi.season
    WHERE pf.season = %s
    ORDER BY pf.player_id, pf.total_z_score DESC
    """
    
    try:
        df = pd.read_sql(query, engine, params=(season,))
        
        # Clean and process the data
        df = df.drop_duplicates(subset=["player_id"])
        df["adp"] = df["adp"].fillna(999)
        df["position"] = df["position"].fillna("N/A")
        df["injury_notes"] = df["injury_notes"].fillna("")
        
        # Add derived metrics
        df["is_injured"] = df["injury_notes"].str.len() > 0
        df["games_played_pct"] = df["games_played"] / 82.0  # Assuming 82 game season
        
        # Sort by total z-score descending
        df = df.sort_values("total_z_score", ascending=False).reset_index(drop=True)
        
        return df
        
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
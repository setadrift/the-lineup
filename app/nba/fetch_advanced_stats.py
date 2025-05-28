import requests
import pandas as pd
import time
from typing import Dict, Optional, List
from datetime import datetime

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://www.nba.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

URL = "https://stats.nba.com/stats/leaguedashplayerstats"

def fetch_advanced_stats(season: str = "2023-24", measure_type: str = "Advanced") -> pd.DataFrame:
    """
    Fetch advanced stats from NBA API.
    
    Args:
        season: NBA season (e.g., "2023-24")
        measure_type: Type of stats to fetch ("Advanced", "Usage", "Misc", etc.)
        
    Returns:
        DataFrame with advanced stats
    """
    params = {
        "Season": season,
        "SeasonType": "Regular Season",
        "MeasureType": measure_type,
        "PerMode": "PerGame",
        "LeagueID": "00",
        "LastNGames": "0",
        "Month": "0",
        "OpponentTeamID": "0",
        "PORound": "0",
        "Period": "0",
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "SeasonSegment": "",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "TwoWay": "0",
        "VsConference": "",
        "VsDivision": ""
    }

    try:
        time.sleep(1)  # Rate limiting
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]

        df = pd.DataFrame(rows, columns=headers)
        print(f"✅ Fetched {len(df)} rows of {measure_type} stats for {season}")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {measure_type} stats: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")
        raise

def fetch_per_36_stats(season: str = "2023-24") -> pd.DataFrame:
    """
    Fetch per-36 minute stats from NBA API.
    
    Args:
        season: NBA season (e.g., "2023-24")
        
    Returns:
        DataFrame with per-36 stats
    """
    params = {
        "Season": season,
        "SeasonType": "Regular Season",
        "MeasureType": "Base",
        "PerMode": "Per36",  # This gives us per-36 minute stats
        "LeagueID": "00",
        "LastNGames": "0",
        "Month": "0",
        "OpponentTeamID": "0",
        "PORound": "0",
        "Period": "0",
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "SeasonSegment": "",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "TwoWay": "0",
        "VsConference": "",
        "VsDivision": ""
    }

    try:
        time.sleep(1)  # Rate limiting
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]

        df = pd.DataFrame(rows, columns=headers)
        print(f"✅ Fetched {len(df)} rows of Per-36 stats for {season}")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching Per-36 stats: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")
        raise

def fetch_usage_stats(season: str = "2023-24") -> pd.DataFrame:
    """
    Fetch usage and efficiency stats from NBA API.
    
    Args:
        season: NBA season (e.g., "2023-24")
        
    Returns:
        DataFrame with usage stats
    """
    return fetch_advanced_stats(season, "Usage")

def fetch_misc_stats(season: str = "2023-24") -> pd.DataFrame:
    """
    Fetch miscellaneous advanced stats from NBA API.
    
    Args:
        season: NBA season (e.g., "2023-24")
        
    Returns:
        DataFrame with misc stats
    """
    return fetch_advanced_stats(season, "Misc")

def clean_advanced_stats(df: pd.DataFrame, stat_type: str = "Advanced") -> pd.DataFrame:
    """
    Clean and normalize advanced stats data.
    
    Args:
        df: Raw stats DataFrame
        stat_type: Type of stats being cleaned
        
    Returns:
        Cleaned DataFrame with normalized column names
    """
    # Drop exact duplicate rows
    df = df.drop_duplicates(subset=["PLAYER_ID"])
    
    # Remove rows with obviously broken data
    df = df[df["GP"] > 0]  # Must have played at least 1 game
    
    # Base column mapping
    rename_map = {
        "PLAYER_ID": "player_id",
        "TEAM_ABBREVIATION": "team",
        "AGE": "age",
        "GP": "games_played",
        "MIN": "minutes_per_game"
    }
    
    # Add specific mappings based on stat type
    if stat_type == "Advanced":
        rename_map.update({
            "USG_PCT": "usage_rate",
            "TS_PCT": "true_shooting_pct",
            "EFG_PCT": "effective_fg_pct",
            "PIE": "player_efficiency_rating",
            "OREB_PCT": "offensive_rebound_pct",
            "DREB_PCT": "defensive_rebound_pct",
            "REB_PCT": "total_rebound_pct",
            "AST_PCT": "assist_pct",
            "STL_PCT": "steal_pct",
            "BLK_PCT": "block_pct",
            "TOV_PCT": "turnover_pct"
        })
    elif stat_type == "Per36":
        rename_map.update({
            "PTS": "points_per_36",
            "REB": "rebounds_per_36",
            "AST": "assists_per_36",
            "STL": "steals_per_36",
            "BLK": "blocks_per_36",
            "TOV": "turnovers_per_36"
        })
    elif stat_type == "Usage":
        rename_map.update({
            "USG_PCT": "usage_rate",
            "PCT_FGA": "shot_attempt_pct",
            "PCT_FG3A": "three_point_attempt_rate",
            "PCT_FTA": "free_throw_rate"
        })
    elif stat_type == "Misc":
        rename_map.update({
            "PTS_OFF_TOV": "points_off_turnovers",
            "PTS_2ND_CHANCE": "second_chance_points",
            "PTS_FB": "fast_break_points",
            "PTS_PAINT": "points_in_paint"
        })
    
    # Apply renaming for columns that exist
    existing_columns = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_columns)
    
    # Convert percentages from 0-100 to 0-1 scale where appropriate
    percentage_columns = [
        'usage_rate', 'true_shooting_pct', 'effective_fg_pct',
        'offensive_rebound_pct', 'defensive_rebound_pct', 'total_rebound_pct',
        'assist_pct', 'steal_pct', 'block_pct', 'turnover_pct',
        'three_point_attempt_rate', 'free_throw_rate'
    ]
    
    for col in percentage_columns:
        if col in df.columns:
            df[col] = df[col] / 100.0
    
    # Keep only columns we want
    return df[list(existing_columns.values())]

def fetch_all_advanced_stats(season: str = "2023-24") -> Dict[str, pd.DataFrame]:
    """
    Fetch all types of advanced stats and return as dictionary.
    
    Args:
        season: NBA season (e.g., "2023-24")
        
    Returns:
        Dictionary with different stat types as keys and DataFrames as values
    """
    stats_data = {}
    
    print(f"🏀 Fetching all advanced stats for {season}...")
    
    # Fetch different stat types
    try:
        # Advanced stats (efficiency, usage, etc.)
        advanced_df = fetch_advanced_stats(season, "Advanced")
        stats_data["advanced"] = clean_advanced_stats(advanced_df, "Advanced")
        
        # Per-36 minute stats
        per36_df = fetch_per_36_stats(season)
        stats_data["per36"] = clean_advanced_stats(per36_df, "Per36")
        
        # Usage stats
        usage_df = fetch_usage_stats(season)
        stats_data["usage"] = clean_advanced_stats(usage_df, "Usage")
        
        # Miscellaneous stats
        misc_df = fetch_misc_stats(season)
        stats_data["misc"] = clean_advanced_stats(misc_df, "Misc")
        
        print(f"✅ Successfully fetched all advanced stats for {season}")
        
    except Exception as e:
        print(f"❌ Error fetching advanced stats: {e}")
        raise
    
    return stats_data

def merge_advanced_stats(stats_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge all advanced stats into a single DataFrame.
    
    Args:
        stats_data: Dictionary of DataFrames from fetch_all_advanced_stats
        
    Returns:
        Merged DataFrame with all advanced stats
    """
    if not stats_data:
        return pd.DataFrame()
    
    # Start with the first DataFrame
    merged_df = None
    
    for stat_type, df in stats_data.items():
        if df.empty:
            continue
            
        if merged_df is None:
            merged_df = df.copy()
        else:
            # Merge on player_id, keeping all columns
            merged_df = pd.merge(
                merged_df, 
                df, 
                on=['player_id'], 
                how='outer',
                suffixes=('', f'_{stat_type}')
            )
    
    # Add timestamp
    merged_df['last_updated'] = datetime.utcnow()
    
    return merged_df

if __name__ == "__main__":
    # Test the functions
    season = "2023-24"
    
    # Fetch all advanced stats
    all_stats = fetch_all_advanced_stats(season)
    
    # Merge into single DataFrame
    merged_stats = merge_advanced_stats(all_stats)
    
    print(f"\n📊 Final merged stats shape: {merged_stats.shape}")
    print(f"📊 Columns: {list(merged_stats.columns)}")
    print(f"\n🔍 Sample data:")
    print(merged_stats.head()) 
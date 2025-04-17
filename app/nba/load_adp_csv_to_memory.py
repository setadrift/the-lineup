# app/nba/load_adp_csv_to_memory.py

import os
import pandas as pd

def load_adp_data(season: str) -> pd.DataFrame:
    """
    Loads and cleans the ADP CSV for the given season.
    
    Args:
        season (str): e.g. '2022-23'
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with player names and ADP rank.
    """
    # Map season to filename
    season_to_filename = {
        "2018-19": "2018_19_adp.csv",
        "2019-20": "2019_20_adp.csv",
        "2020-21": "2020_21_adp.csv",
        "2021-22": "2021_22_adp.csv",
        "2022-23": "2022_23_adp.csv",
        "2023-24": "2023_24_adp.csv",
    }
    
    file_name = season_to_filename.get(season)
    if not file_name:
        raise ValueError(f"No ADP CSV available for season {season}")
    
    file_path = os.path.join(
        os.path.dirname(__file__), "../data/adp", file_name
    )
    
    # Load
    df = pd.read_csv(file_path)

    # Drop rows where "Rank" is NaN or contains "Rank"
    df = df[df['Rank'].notna()]
    df = df[df['Rank'] != "Rank"]

    # Only keep relevant columns
    df_clean = df[['Player', 'Rank']].copy()
    df_clean['Rank'] = df_clean['Rank'].astype(int)
    df_clean['Player'] = df_clean['Player'].str.strip()

    return df_clean

if __name__ == "__main__":
    season = "2022-23"
    df_adp = load_adp_data(season)
    print(df_adp.head(20))

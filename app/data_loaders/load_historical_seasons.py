import sys
import os
import time

# Set up project path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.etl.insert_players import insert_players, extract_player_data
from app.etl.insert_player_stats import insert_player_stats
from app.etl.insert_game_logs import fetch_player_game_logs, normalize_game_log_data, insert_player_game_logs
from app.etl.insert_team_schedule import fetch_team_schedule, normalize_team_schedule, insert_team_schedule
from app.data_loaders.fetch_season_stats import fetch_nba_stats, clean_player_stats

SEASONS = ["2022-23", "2021-22", "2020-21", "2019-20", "2018-19"]

def load_all_data_for_season(season):
    print(f"📦 Loading data for {season}...")

    # 1. Player Stats
    df_stats_raw = fetch_nba_stats(season=season)
    df_stats_clean = clean_player_stats(df_stats_raw)
    insert_player_stats(df_stats_clean, season)

    # 2. Players (upsert safe)
    df_players = extract_player_data(df_stats_raw)
    insert_players(df_players)

    # 3. Game Logs
    df_logs_raw = fetch_player_game_logs(season)
    df_logs_clean = normalize_game_log_data(df_logs_raw)
    insert_player_game_logs(df_logs_clean)

    # 4. Schedule
    df_sched_raw = fetch_team_schedule(season)
    df_sched_clean = normalize_team_schedule(df_sched_raw, season)
    insert_team_schedule(df_sched_clean)

    time.sleep(1)  # Avoid hammering the NBA API

if __name__ == "__main__":
    for season in SEASONS:
        try:
            load_all_data_for_season(season)
        except Exception as e:
            print(f"❌ Failed to load {season}: {e}")
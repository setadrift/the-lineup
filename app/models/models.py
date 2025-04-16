from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    team = Column(String, nullable=True)
    position = Column(String, nullable=True)
    status = Column(String, default="Active")
    bbm_rank = Column(Float, nullable=True)
    bbm_value = Column(Float, nullable=True)
    adp = Column(Float, nullable=True)
    games_played = Column(Integer, default=0)
    injury_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PlayerStats(Base):
    __tablename__ = "player_stats"

    stats_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer)
    season = Column(String)  # e.g., "2023-24"
    team = Column(String)
    games_played = Column(Integer)
    minutes_per_game = Column(Float)
    points_per_game = Column(Float)
    rebounds_per_game = Column(Float)
    assists_per_game = Column(Float)
    steals_per_game = Column(Float)
    blocks_per_game = Column(Float)
    turnovers_per_game = Column(Float)
    fg_pct = Column(Float)
    ft_pct = Column(Float)
    three_pm = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    game_stats_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, nullable=False)
    game_date = Column(DateTime, nullable=False)
    opponent_team = Column(String)
    home_or_away = Column(String)  # "H" or "A"
    minutes = Column(Float)
    points = Column(Integer)
    rebounds = Column(Integer)
    assists = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    turnovers = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    ftm = Column(Integer)
    fta = Column(Integer)
    three_pm = Column(Integer)
    plus_minus = Column(Integer)
    fantasy_points = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)


class TeamSchedule(Base):
    __tablename__ = "team_schedule"

    game_id = Column(Integer, primary_key=True, index=True)
    game_date = Column(DateTime, nullable=False)
    team = Column(String, nullable=False)
    opponent_team = Column(String)
    home_or_away = Column(String)  # "H" or "A"
    game_time = Column(DateTime, nullable=True)
    season = Column(String)
    is_back_to_back = Column(Boolean, default=False)
    is_high_volume_day = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PlayerFeatures(Base):
    __tablename__ = "player_features"

    feature_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, index=True)
    season = Column(String)

    z_points = Column(Float)
    z_rebounds = Column(Float)
    z_assists = Column(Float)
    z_steals = Column(Float)
    z_blocks = Column(Float)
    z_turnovers = Column(Float)
    z_fg_pct = Column(Float)
    z_ft_pct = Column(Float)
    z_three_pm = Column(Float)
    total_z_score = Column(Float)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PlayerSeasonInfo(Base):
    __tablename__ = "player_season_info"

    season_info_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, index=True, nullable=False)
    season = Column(String, nullable=False)
    adp = Column(Float, nullable=True)  # Average draft position
    injury_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

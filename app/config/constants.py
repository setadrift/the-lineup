"""
Constants and configuration values used across the application.
"""

# Team-specific pace factors for projections
PACE_FACTORS = {
    'PHI': 0.95,
    'OKC': 1.05,
    'DEN': 1.00,
    # Add more as needed
}

# Player-specific injury risk factors
INJURY_RISK = {
    'Joel Embiid': 0.85,
    'Shai Gilgeous-Alexander': 0.95,
    'Nikola Jokic': 1.00,
    # Add more as needed
}

# NBA API configuration
NBA_API_CONFIG = {
    "BASE_URL": "https://stats.nba.com/stats",
    "HEADERS": {
        "Host": "stats.nba.com",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Referer": "https://www.nba.com/",
        "Connection": "keep-alive"
    }
}

# Supported seasons for historical data
SUPPORTED_SEASONS = [
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24"
]

# Fantasy scoring weights
FANTASY_SCORING = {
    "points": 1.0,
    "rebounds": 1.2,
    "assists": 1.5,
    "steals": 3.0,
    "blocks": 3.0,
    "turnovers": -1.0
} 
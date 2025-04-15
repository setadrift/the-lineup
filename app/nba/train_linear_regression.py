import os
import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to Supabase
engine = create_engine(DATABASE_URL)

def fetch_training_data():
    query = """
    SELECT 
        pf.player_id, pf.season, pf.total_z_score, 
        ps.points_per_game, ps.rebounds_per_game, ps.assists_per_game,
        ps.steals_per_game, ps.blocks_per_game, ps.turnovers_per_game,
        ps.fg_pct, ps.ft_pct, ps.three_pm
    FROM player_features pf
    JOIN player_stats ps 
        ON pf.player_id = ps.player_id AND pf.season = ps.season
    WHERE pf.season IN ('2018-19', '2019-20', '2020-21', '2021-22', '2022-23')
    """
    df = pd.read_sql(query, engine)
    return df.dropna()

def train_model(df):
    features = [
        'points_per_game', 'rebounds_per_game', 'assists_per_game',
        'steals_per_game', 'blocks_per_game', 'turnovers_per_game',
        'fg_pct', 'ft_pct', 'three_pm'
    ]
    X = df[features]
    y = df['total_z_score']

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    print("✅ Model trained.")
    print(f"📉 MSE: {mse:.4f}")
    print(f"📈 R²: {r2:.4f}")

    print("\n🔍 Coefficients:")
    for feat, coef in zip(features, model.coef_):
        print(f"{feat:20} {coef:.4f}")

    return model

if __name__ == "__main__":
    df = fetch_training_data()
    model = train_model(df)

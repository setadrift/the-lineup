import os
import sys
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, project_root)

# Load DB URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

st.set_page_config(layout="wide")
st.title("📊 Fantasy Player Z-Score Projections")

@st.cache_data
def fetch_actual_vs_predicted():
    query = """
    SELECT 
        pf.player_id,
        p.name,
        ps.season,
        pf.total_z_score AS actual_z,
        ps.points_per_game, ps.rebounds_per_game, ps.assists_per_game,
        ps.steals_per_game, ps.blocks_per_game, ps.turnovers_per_game,
        ps.fg_pct, ps.ft_pct, ps.three_pm
    FROM player_features pf
    JOIN player_stats ps ON pf.player_id = ps.player_id AND pf.season = ps.season
    JOIN players p ON p.player_id = pf.player_id
    WHERE pf.season IN ('2018-19', '2019-20', '2020-21', '2021-22', '2022-23')
    """
    df = pd.read_sql(query, engine)

    # Predict using same logic as linear regression model
    from sklearn.linear_model import LinearRegression

    X = df[[
        'points_per_game', 'rebounds_per_game', 'assists_per_game',
        'steals_per_game', 'blocks_per_game', 'turnovers_per_game',
        'fg_pct', 'ft_pct', 'three_pm'
    ]]
    y = df["actual_z"]
    model = LinearRegression()
    model.fit(X, y)
    df["predicted_z"] = model.predict(X)
    df["error"] = df["predicted_z"] - df["actual_z"]
    return df


df = fetch_actual_vs_predicted()

# Sidebar filters
season = st.sidebar.selectbox("Season", sorted(df["season"].unique(), reverse=True))
df_filtered = df[df["season"] == season]

st.markdown(f"### 🔍 Predicted vs Actual Z-Score ({season})")
st.dataframe(
    df_filtered[["name", "actual_z", "predicted_z", "error"]].sort_values(by="actual_z", ascending=False),
    use_container_width=True
)

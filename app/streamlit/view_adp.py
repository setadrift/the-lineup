import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

query = """
SELECT p.name, psi.season, psi.adp
FROM player_season_info psi
JOIN players p ON psi.player_id = p.player_id
WHERE psi.adp IS NOT NULL
ORDER BY psi.season, psi.adp
"""
df = pd.read_sql(query, engine)

st.title("🏀 ADP by Season")

for season in df["season"].unique():
    st.subheader(f"Season {season}")
    top_players = df[df["season"] == season].sort_values("adp").head(10)
    st.dataframe(top_players)

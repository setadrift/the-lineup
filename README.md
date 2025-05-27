# The Lineup - Fantasy Basketball Draft Assistant

A modular fantasy basketball draft assistant tool built with Python (FastAPI) and PostgreSQL (Supabase). Features single-user mock drafting with Yahoo 9-cat league logic and z-score-based stat analysis.

## 🚀 Features

- **Mock Draft Assistant**: AI-powered draft suggestions with z-score analysis
- **📈 Historical Stat Trends**: Mini-sparklines showing player performance trends over multiple seasons
- **Real-time Player Analysis**: Z-score breakdowns for all 9-category stats
- **Intelligent Pick Suggestions**: Context-aware recommendations based on team needs
- **Draft Progress Tracking**: Visual draft status and team roster management

## 🏀 Historical Trends Feature

The new **Historical Stat Trends** feature provides:

- **Mini-sparklines** for key fantasy basketball stats (last 3 seasons)
- **Trend analysis** (increasing, decreasing, stable, volatile)
- **Draft insights** based on player trajectory
- **Season-by-season breakdowns** with performance metrics

Access via the "📊 Historical Trends" tab in the detailed player stats section.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (Supabase)
- **Frontend**: Streamlit, Plotly (for sparklines)
- **Data Processing**: Pandas, NumPy
- **Data Source**: NBA Stats API (2018-19 to current season)

## 🚀 Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Start the API server: `uvicorn app.main:app --reload`
3. Run the draft assistant: `streamlit run app/frontend/streamlit/pages/draft_assistant_v2.py`
4. Navigate to the Historical Trends tab in player details for trend analysis

```bash
uvicorn app.main:app --reload

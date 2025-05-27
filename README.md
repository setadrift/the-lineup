# The Lineup - Fantasy Basketball Draft Assistant

A modular fantasy basketball draft assistant tool built with Python (FastAPI) and PostgreSQL (Supabase). Features single-user mock drafting with Yahoo 9-cat league logic and z-score-based stat analysis.

## 🚀 Features

- **Mock Draft Assistant**: AI-powered draft suggestions with z-score analysis
- **📈 Historical Stat Trends**: Mini-sparklines showing player performance trends over multiple seasons
- **⚖️ Player Comparison Tool**: Side-by-side player analysis with radar charts and intelligent recommendations
- **Real-time Player Analysis**: Z-score breakdowns for all 9-category stats
- **Intelligent Pick Suggestions**: Context-aware recommendations based on team needs
- **Draft Progress Tracking**: Visual draft status and team roster management

## 🏀 Advanced Analytics Features

### Historical Stat Trends
- **Mini-sparklines** for key fantasy basketball stats (last 3 seasons)
- **Trend analysis** (increasing, decreasing, stable, volatile)
- **Draft insights** based on player trajectory
- **Season-by-season breakdowns** with performance metrics

### Player Comparison Tool
- **Side-by-side comparison** of any two players
- **Interactive radar charts** for z-score visualization across 9 categories
- **Statistical breakdowns** with season averages and detailed metrics
- **Historical trend comparison** and draft recommendations
- **Intelligent summary** with winner indicators and category strengths

Access both features via the detailed player stats tabs in the draft assistant.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (Supabase)
- **Frontend**: Streamlit, Plotly (for charts and visualizations)
- **Data Processing**: Pandas, NumPy
- **Data Source**: NBA Stats API (2018-19 to current season)

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

**Using the shell script (macOS/Linux):**
```bash
./start_lineup.sh
```

**Using the batch file (Windows):**
```cmd
start_lineup.bat
```

**Using Python directly (All platforms):**
```bash
python run_full_app.py
```

All methods will:
- ✅ Start the FastAPI backend server (http://localhost:8000)
- ✅ Start the Streamlit frontend (http://localhost:8502)
- ✅ Monitor both processes and restart if needed
- ✅ Handle graceful shutdown with Ctrl+C

### Option 2: Manual Startup

If you prefer to run the servers separately:

**Terminal 1 - Start Backend:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run app/frontend/streamlit/pages/draft_assistant_v2.py --server.port 8502
```

### Option 3: Frontend Only (Limited Features)

For basic functionality without historical trends and player comparison:
```bash
python run_draft_v2.py
```

## 📱 Usage

1. **Open your browser** and go to http://localhost:8502
2. **Configure your draft** in the sidebar (teams, position, season)
3. **Start a mock draft** and follow AI suggestions
4. **Access advanced features** via "📊 View Detailed Player Stats & Z-Scores":
   - **📈 Season Averages** - Current season per-game statistics
   - **⚡ Z-Score Breakdown** - Statistical rankings across all categories
   - **📊 Historical Trends** - Multi-season performance analysis
   - **⚖️ Player Comparison** - Side-by-side player analysis tool

## 🔧 API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation.

```bash
uvicorn app.main:app --reload

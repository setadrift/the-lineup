from fastapi import FastAPI
from app.routers import historical_stats

app = FastAPI(
    title="The Lineup - Fantasy Basketball Draft Assistant",
    description="A modular fantasy basketball draft assistant with historical stat trends and z-score analysis",
    version="1.0.0"
)

# Include routers
app.include_router(historical_stats.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to The Lineup - Fantasy Basketball Draft Assistant"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "The Lineup API"}

if __name__ == "__main__":
    df_raw = fetch_nba_stats()
    df_clean = clean_player_stats(df_raw)

    print(df_clean.head())
    print("✅ Cleaned & normalized rows:", len(df_clean))

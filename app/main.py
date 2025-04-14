from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to The Lineup"}

if __name__ == "__main__":
    df_raw = fetch_nba_stats()
    df_clean = clean_player_stats(df_raw)

    print(df_clean.head())
    print("✅ Cleaned & normalized rows:", len(df_clean))

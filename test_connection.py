from app.db.connection import SessionLocal
from sqlalchemy import text

def test_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Connection Successful!")
    except Exception as e:
        print("❌ Connection Failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_db_connection()

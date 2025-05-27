from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Create the connection URL using components
connection_url = URL.create(
    drivername="postgresql",
    username="postgres.rajazhsbfwxgznzgrfdh",
    password="y42-wQce@Nv!Ka&",
    host="aws-0-us-east-1.pooler.supabase.com",
    port=5432,
    database="postgres",
    query={"sslmode": "require"}
)

engine = create_engine(connection_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency function to get database session for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

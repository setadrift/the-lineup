"""
Database utility functions and context managers.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.db.connection import SessionLocal

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db() as session:
            results = session.query(Model).all()
    
    Yields:
        Session: Database session that will be automatically closed
    """
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def safe_commit(session: Session, error_msg: str = "Database operation failed") -> bool:
    """
    Safely commit database changes with error handling.
    
    Args:
        session (Session): SQLAlchemy session
        error_msg (str): Custom error message for failures
        
    Returns:
        bool: True if commit succeeded, False if it failed
    """
    try:
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ {error_msg}: {e}")
        return False

def batch_upsert(session: Session, model, records: list, batch_size: int = 100) -> bool:
    """
    Perform batch upsert operations with error handling.
    
    Args:
        session (Session): SQLAlchemy session
        model: SQLAlchemy model class
        records (list): List of model instances to upsert
        batch_size (int): Number of records per batch
        
    Returns:
        bool: True if all batches succeeded, False if any failed
    """
    try:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Delete existing records in this batch
            ids = [record.id for record in batch]
            session.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
            
            # Add new records
            session.bulk_save_objects(batch)
            session.commit()
            
            print(f"✅ Processed batch {i//batch_size + 1} ({len(batch)} records)")
            
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Batch operation failed: {e}")
        return False 
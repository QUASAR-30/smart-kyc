"""
SmartKYC - Database Configuration
SQLAlchemy database connection and session management
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from app.models.base import Base

# Load environment variables
load_dotenv()

# Database URL from environment
# Database URL from environment
# FORCE SQLITE to bypass MySQL auth issues in local development
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartkyc.db")
DATABASE_URL = "sqlite:///./smartkyc.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",  # Echo SQL queries in debug mode
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        SQLAlchemy session

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be run once when setting up the application.
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def drop_all_tables() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data! Use only in development.
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")


if __name__ == "__main__":
    # For testing: Create tables
    print("Creating database tables...")
    init_db()

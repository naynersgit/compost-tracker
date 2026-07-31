from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
 
# During local development we use SQLite — zero setup, just a file on disk.
# In production, DATABASE_URL will point at a real Postgres database instead.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./compost.db")
 
# Some hosts (Railway included) hand out URLs starting with "postgres://",
# but SQLAlchemy 2.x requires "postgresql://" — this line fixes that mismatch.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
 
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
 
def get_db():
    """FastAPI dependency: gives each request its own DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
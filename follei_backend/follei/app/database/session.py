import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", # It's best practice to set this as an environment variable
    "postgresql://postgres:YOUR_CORRECT_PASSWORD@127.0.0.1:5432/follei_db", # Replace YOUR_CORRECT_PASSWORD
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

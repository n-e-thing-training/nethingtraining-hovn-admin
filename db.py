from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = "postgresql://neondb_owner:npg_xlz8Uq2omAMW@ep-weathered-waterfall-a82hrp3w-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

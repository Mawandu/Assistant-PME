# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

# FIX: Common mistake checking
if DATABASE_URL.startswith("http"):
    raise ValueError(
        "❌ ERREUR DE CONFIGURATION : Vous avez utilisé une URL HTTP (Site Web) comme DATABASE_URL.\n"
        "👉 Vous devez utiliser la 'Connection String' (URI) de Supabase.\n"
        "Format attendu : postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
    )

# FIX: SQLAlchemy often requires postgresql:// instead of postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session in API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

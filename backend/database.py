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

# FIX: Handle unencoded special characters in password (like @)
try:
    prefix = "postgresql://"
    # Masking function for logs
    def mask_url(url):
        try:
            if "@" in url:
                part1, part2 = url.rsplit("@", 1)
                if ":" in part1:
                    u, p = part1.split(":", 1)
                    return f"{u}:******@{part2}"
            return "******"
        except:
            return "******"

    print(f"🔍 DEBUG: Raw DATABASE_URL: {mask_url(DATABASE_URL)}")

    if DATABASE_URL.startswith(prefix) and DATABASE_URL.count("@") > 1:
        import urllib.parse
        # Check if we have multiple @, which implies one is in the password
        # Format: postgresql://user:password@host:port/db
        # We split from the right to separate host from credentials
        rest = DATABASE_URL[len(prefix):]
        if "@" in rest:
            creds, host_part = rest.rsplit("@", 1)
            if ":" in creds:
                user, password = creds.split(":", 1)
                # Check if password needs encoding (look for unencoded @)
                if "@" in password and "%40" not in password:
                    print(f"⚠️  Detecting unencoded '@' in password. Auto-fixing...")
                    fixed_password = urllib.parse.quote_plus(password)
                    DATABASE_URL = f"{prefix}{user}:{fixed_password}@{host_part}"
                    print(f"✅ Fixed DATABASE_URL: {mask_url(DATABASE_URL)}")
    
    # Verify with make_url
    from sqlalchemy.engine import make_url
    u = make_url(DATABASE_URL)
    print(f"🔍 DEBUG: SQLAlchemy Parsed Host: {u.host}")
    print(f"🔍 DEBUG: SQLAlchemy Parsed Port: {u.port}")
    print(f"🔍 DEBUG: SQLAlchemy Parsed Database: {u.database}")

except Exception as e:
    print(f"⚠️  Error attempting to fix/debug DATABASE_URL: {e}")


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session in API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

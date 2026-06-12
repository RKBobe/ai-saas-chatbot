from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Attempt to connect to PostgreSQL, fall back to SQLite if it fails
try:
    engine = create_engine(
        settings.DATABASE_URL, 
        pool_pre_ping=True
    )
    # Test connection briefly
    with engine.connect() as conn:
        print("[OK] Connected to PostgreSQL database")
except Exception:
    print("[WARNING] PostgreSQL connection failed. Falling back to local SQLite database: sqlite:///./saas_db.db")
    engine = create_engine(
        "sqlite:///./saas_db.db",
        connect_args={"check_same_thread": False}
    )

# Create a Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
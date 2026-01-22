from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the engine that connects to PostgreSQL
# pool_pre_ping=True helps prevent "server closed the connection unexpectedly" errors
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# Create a Session factory. 
# We call SessionLocal() whenever we need to talk to the DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
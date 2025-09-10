from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the SQLAlchemy engine
# The 'pool_pre_ping' argument helps prevent "database has gone away" errors
# by checking the connection's validity before using it.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create a configured "Session" class
# This is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
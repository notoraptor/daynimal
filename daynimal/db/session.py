from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from daynimal.config import settings


def get_engine():
    """Create and return SQLAlchemy engine."""
    return create_engine(settings.database_url, echo=False)


def get_session() -> Session:
    """Create and return a new database session."""
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    return session_factory()

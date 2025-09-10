from app.db.session import SessionLocal

def get_db():
    """
    FastAPI dependency that provides a database session for a single request.
    Ensures the session is always closed, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
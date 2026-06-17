import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Adjust the path to find the app module if necessary.
# Within app/tests, 'from ..database' should work if run via pytest from the app root.
# However, to ensure pytest finds 'app', let's add the parent directory to the path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..database import Base, get_db
from .. import models # Ensure models are loaded
from ..main import app

from sqlalchemy.pool import StaticPool

# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after the test to ensure complete isolation
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    # Override get_db dependency to use the test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # Cleanup is handled by the db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Clear overrides after the test
    app.dependency_overrides.clear()

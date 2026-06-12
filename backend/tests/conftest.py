import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure the app directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Override environment variables for isolation during tests
os.environ["DATABASE_URL"] = "sqlite:///./test_saas_db.db"
os.environ["GEMINI_API_KEY"] = "mock-key-for-testing"

from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.services.llm.gemini_service import GeminiService
from unittest.mock import AsyncMock

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    # Create all tables at the start of the test session
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables and clean up the file
    Base.metadata.drop_all(bind=engine)
    try:
        if os.path.exists("./test_saas_db.db"):
            os.remove("./test_saas_db.db")
    except Exception:
        pass

@pytest.fixture
def client():
    # Use the FastAPI TestClient to simulate requests to our API
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_gemini():
    # Provide a mock GeminiService to avoid actual API calls
    mock = AsyncMock(spec=GeminiService)
    mock.generate_response.return_value = "This is a mock AI response."
    return mock

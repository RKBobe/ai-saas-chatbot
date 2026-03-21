import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure the app directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.services.llm.gemini_service import GeminiService
from unittest.mock import AsyncMock

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

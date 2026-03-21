import pytest
from app.services.llm.vector_store import VectorStoreService
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.config import settings

# Mock the entire get_chroma_client to prevent connection attempts during test discovery
@pytest.fixture(autouse=True)
def mock_chroma():
    with patch("app.services.llm.vector_store.get_chroma_client") as mock_get:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_get.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Setup default search response
        mock_collection.query.return_value = {"documents": [[]]}
        
        yield mock_collection

@pytest.mark.anyio
async def test_multi_tenancy_isolation(mock_chroma):
    """
    Verify that VectorStoreService correctly targets client-specific collections.
    """
    client_a_id = "test_client_a"
    service_a = VectorStoreService(client_id=client_a_id)
    
    assert service_a.collection_name == f"client_{client_a_id}_memories"
    
    # Test adding memory calls the correct collection method
    await service_a.add_memory("fact", {"id": "1"})
    mock_chroma.add.assert_called_once()

def test_root_endpoint(client):
    """Test the API's root endpoint for basic availability."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_chat_endpoint_structure(client):
    """Test the POST /chat endpoint responds with the correct JSON structure."""
    with patch("app.api.v1.endpoints.chat.llm_service.generate_response", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Mocked AI Response"
        
        test_payload = {
            "message": "Hello world",
            "client_id": "test-suite-client",
            "user_id": "test-suite-user"
        }
        
        response = client.post("/api/v1/chat/", json=test_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Mocked AI Response"
        assert data["client_id"] == "test-suite-client"
        assert data["user_id"] == "test-suite-user"

def test_facebook_webhook_handshake_failure(client):
    """Test that the webhook fails verification with an incorrect token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "WRONG_TOKEN",
        "hub.challenge": "12345"
    }
    response = client.get("/api/v1/webhooks/facebook", params=params)
    assert response.status_code == 403
    assert "Verification token mismatch" in response.json()["detail"]

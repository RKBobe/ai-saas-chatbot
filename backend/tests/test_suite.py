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
    with patch("app.api.v1.endpoints.chat.OfficeAgent.get_response", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = "Mocked AI Response"
        
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


def test_inventory_crud(client):
    """Test CRUD operations on the Inventory API endpoints."""
    payload = {
        "sku": "SKU-TEST-999",
        "name": "Test Item Name",
        "description": "Test Item Description",
        "price": 49.99,
        "stock_quantity": 10
    }
    # 1. Create
    response = client.post("/api/v1/inventory/?client_id=test_client", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == "SKU-TEST-999"
    assert data["name"] == "Test Item Name"
    assert data["price"] == 49.99
    assert data["stock_quantity"] == 10
    item_id = data["id"]

    # 2. Get all
    response = client.get("/api/v1/inventory/?client_id=test_client")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any(i["sku"] == "SKU-TEST-999" for i in items)

    # 3. Search query
    response = client.get("/api/v1/inventory/?client_id=test_client&query=Item")
    assert response.status_code == 200
    items_search = response.json()
    assert any(i["sku"] == "SKU-TEST-999" for i in items_search)

    # 4. Delete
    response = client.delete(f"/api/v1/inventory/{item_id}?client_id=test_client")
    assert response.status_code == 200

    # Verify deleted
    response = client.get("/api/v1/inventory/?client_id=test_client")
    items_after = response.json()
    assert not any(i["sku"] == "SKU-TEST-999" for i in items_after)


def test_inventory_csv_upload(client):
    """Test CSV file ingestion endpoint for inventory seeding."""
    csv_content = (
        "sku,name,price,stock_quantity,description\n"
        "SKU-CSV-1,CSV Item 1,9.99,100,CSV desc 1\n"
        "SKU-CSV-2,CSV Item 2,19.99,50,CSV desc 2\n"
    )
    files = {"file": ("test_inventory.csv", csv_content, "text/csv")}
    response = client.post("/api/v1/inventory/upload-csv?client_id=csv_client", files=files)
    assert response.status_code == 200
    assert "Successfully imported/updated 2 items." in response.json()["message"]

    response = client.get("/api/v1/inventory/?client_id=csv_client")
    items = response.json()
    assert len(items) == 2
    assert any(i["sku"] == "SKU-CSV-1" for i in items)


def test_appointments_crud(client):
    """Test appointment scheduling, listing, and overlap validation endpoints."""
    payload = {
        "customer_name": "Test Customer",
        "customer_phone": "+1234567890",
        "start_time": "2026-06-20T10:00:00",
        "notes": "Test appointment notes",
        "status": "scheduled"
    }
    # 1. Create
    response = client.post("/api/v1/appointments/?client_id=apt_client", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Test Customer"
    assert data["customer_phone"] == "+1234567890"
    apt_id = data["id"]

    # 2. Get all
    response = client.get("/api/v1/appointments/?client_id=apt_client")
    assert response.status_code == 200
    apts = response.json()
    assert len(apts) >= 1
    assert any(a["id"] == apt_id for a in apts)

    # 3. Get with date filter
    response = client.get("/api/v1/appointments/?client_id=apt_client&date=2026-06-20")
    assert response.status_code == 200
    apts_filtered = response.json()
    assert any(a["id"] == apt_id for a in apts_filtered)

    # 4. Overlap validation
    response = client.post("/api/v1/appointments/?client_id=apt_client", json=payload)
    assert response.status_code == 400
    assert "already booked" in response.json()["detail"]

    # 5. Cancel
    response = client.delete(f"/api/v1/appointments/{apt_id}?client_id=apt_client")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify status changed
    response = client.get("/api/v1/appointments/?client_id=apt_client")
    apts_after = response.json()
    assert any(a["id"] == apt_id and a["status"] == "cancelled" for a in apts_after)


def test_twilio_sms_webhook(client):
    """Test Twilio SMS Webhook integration parsing and dynamic TwiML response."""
    with patch("app.api.v1.endpoints.sms.OfficeAgent.get_response", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = "Test SMS Reply"
        
        form_data = {
            "Body": "Hello SMS",
            "From": "+15559876"
        }
        response = client.post("/api/v1/sms/twilio?client_id=sms_test", data=form_data)
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Message>Test SMS Reply</Message>" in response.text


def test_twilio_voice_webhooks(client):
    """Test Twilio Voice call start and transcription process turns."""
    # 1. Start call
    form_data_start = {
        "From": "+15551111"
    }
    response = client.post("/api/v1/voice/twilio?client_id=voice_test", data=form_data_start)
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Gather" in response.text
    assert 'input="speech"' in response.text
    assert "Hello! Welcome to our office assistant. How can I help you today?" in response.text

    # 2. Process turn
    with patch("app.api.v1.endpoints.voice.OfficeAgent.get_response", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = "Test Voice Reply"
        
        form_data_process = {
            "From": "+15551111",
            "SpeechResult": "Simulated spoken text"
        }
        response = client.post("/api/v1/voice/twilio/process?client_id=voice_test", data=form_data_process)
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Gather" in response.text
        assert 'input="speech"' in response.text
        assert "<Say>Test Voice Reply</Say>" in response.text


def test_agent_tools_directly():
    """Test Office Agent tool definitions directly against isolated DB engine."""
    from app.services.agent.tools import (
        check_inventory,
        book_appointment,
        check_availability,
        current_client_id
    )
    from app.models.inventory import Inventory
    from app.db.session import SessionLocal

    token = current_client_id.set("tools_test_client")
    db = SessionLocal()
    item = Inventory(
        client_id="tools_test_client",
        sku="SKU-TOOL-1",
        name="Tool Test Item",
        price=10.0,
        stock_quantity=5,
        description="Tool test desc"
    )
    db.add(item)
    db.commit()

    try:
        # Check stock levels
        result = check_inventory("SKU-TOOL-1")
        assert "Tool Test Item" in result
        assert "5 units" in result

        # Check calendar times
        avail_result = check_availability("2026-07-01")
        assert "Available appointment times for 2026-07-01" in avail_result

        # Book slot
        booking_result = book_appointment(
            customer_name="Tool Cust",
            customer_phone="+12345",
            date_str="2026-07-01",
            time_str="10:00 AM"
        )
        assert "Success!" in booking_result
        assert "Date: 2026-07-01" in booking_result
        assert "10:00 AM" in booking_result

        # Check slot is booked
        avail_after = check_availability("2026-07-01")
        assert "10:00 AM" not in avail_after
    finally:
        db.query(Inventory).filter(Inventory.client_id == "tools_test_client").delete()
        db.commit()
        db.close()
        current_client_id.reset(token)


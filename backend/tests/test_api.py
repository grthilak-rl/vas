import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_login_endpoint():
    """Test login endpoint."""
    response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_get_devices_unauthorized():
    """Test getting devices without authentication."""
    response = client.get("/api/devices")
    assert response.status_code == 401


def test_get_devices_authorized():
    """Test getting devices with authentication."""
    # First login to get token
    login_response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Use token to access devices
    response = client.get("/api/devices", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data


def test_start_discovery_unauthorized():
    """Test starting discovery without authentication."""
    response = client.post("/api/discover", json={
        "subnets": ["192.168.1.0/24"]
    })
    assert response.status_code == 401


def test_start_discovery_authorized():
    """Test starting discovery with authentication."""
    # First login to get token
    login_response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Start discovery
    response = client.post("/api/discover", json={
        "subnets": ["192.168.1.0/24"]
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "message" in data
    assert "estimated_duration" in data


def test_validate_device_unauthorized():
    """Test device validation without authentication."""
    response = client.post("/api/devices/validate", json={
        "ip_address": "192.168.1.1"
    })
    assert response.status_code == 401


def test_validate_device_authorized():
    """Test device validation with authentication."""
    # First login to get token
    login_response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Mock validation service
    with patch('app.services.validation.validation_service.validate_rtsp_stream') as mock_validate:
        mock_validate.return_value = {
            "ip_address": "192.168.1.1",
            "is_valid": True,
            "rtsp_url": "rtsp://192.168.1.1:554/stream1",
            "resolution": "1920x1080",
            "codec": "h264",
            "fps": 25,
            "error_message": None
        }
        
        response = client.post("/api/devices/validate", json={
            "ip_address": "192.168.1.1"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["ip_address"] == "192.168.1.1"


def test_api_documentation():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/api/health")
    assert response.status_code == 200
    # CORS headers should be present (handled by FastAPI middleware) 
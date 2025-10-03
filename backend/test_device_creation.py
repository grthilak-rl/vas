#!/usr/bin/env python3
"""
Test script for device creation with authentication
"""

import requests
import json
from datetime import datetime, timedelta
from jose import jwt

# API base URL
BASE_URL = "http://localhost:8000/api"

# Demo admin credentials (from auth service)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# JWT settings (from config)
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_test_token():
    """Create a test JWT token for the admin user."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": ADMIN_USERNAME,
        "username": ADMIN_USERNAME,
        "role": "admin",
        "full_name": "Administrator",
        "exp": expire
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def test_device_creation():
    """Test creating a device with proper authentication."""
    
    # Create test token
    token = create_test_token()
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Test device data
    device_data = {
        "name": "Test Camera 1",
        "device_type": "IP Camera",
        "manufacturer": "Test Corp",
        "model": "TC-100",
        "ip_address": "192.168.1.100",
        "port": 554,
        "rtsp_url": "rtsp://192.168.1.100:554/stream",
        "username": "admin",
        "password": "password123",
        "location": "Test Room 1",
        "description": "Test camera for validation",
        "tags": ["test", "camera", "indoor"],
        "metadata": {
            "resolution": "1920x1080",
            "fps": 30,
            "codec": "H.264"
        }
    }
    
    print("Testing device creation...")
    print(f"Device data: {json.dumps(device_data, indent=2)}")
    
    try:
        # Create device
        response = requests.post(
            f"{BASE_URL}/devices/",
            headers=headers,
            json=device_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            device = response.json()
            print(f"✅ Device created successfully!")
            print(f"Device ID: {device['id']}")
            print(f"Device Name: {device['name']}")
            print(f"Device IP: {device['ip_address']}")
            
            # Test getting the device
            print("\nTesting device retrieval...")
            get_response = requests.get(
                f"{BASE_URL}/devices/{device['id']}",
                headers=headers
            )
            
            print(f"Get Status Code: {get_response.status_code}")
            if get_response.status_code == 200:
                retrieved_device = get_response.json()
                print(f"✅ Device retrieved successfully!")
                print(f"Retrieved Device: {json.dumps(retrieved_device, indent=2)}")
            else:
                print(f"❌ Failed to retrieve device: {get_response.text}")
                
        else:
            print(f"❌ Failed to create device: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_device_listing():
    """Test listing devices."""
    
    # Create test token
    token = create_test_token()
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("\nTesting device listing...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/devices/",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            devices_response = response.json()
            print(f"✅ Devices listed successfully!")
            print(f"Total devices: {devices_response['total']}")
            print(f"Devices: {json.dumps(devices_response['devices'], indent=2)}")
        else:
            print(f"❌ Failed to list devices: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing VAS Device API with Authentication")
    print("=" * 50)
    
    test_device_creation()
    test_device_listing()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 
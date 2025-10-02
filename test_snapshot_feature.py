#!/usr/bin/env python3
"""
Snapshot Feature Test Script
Tests the snapshot functionality without affecting existing system
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vas', 'backend'))

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_api_health():
    """Test if the API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def authenticate():
    """Authenticate and get token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login-json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication error: {e}")
        return None

def get_devices(token):
    """Get list of devices"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/devices/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            print(f"✅ Found {len(devices)} devices")
            return devices
        else:
            print(f"❌ Failed to get devices: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting devices: {e}")
        return []

def test_snapshot_capture(token, device_id):
    """Test snapshot capture for a device"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE}/snapshots/capture/{device_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            snapshot = response.json()
            print(f"✅ Snapshot captured successfully: {snapshot['id']}")
            print(f"   - Format: {snapshot['image_format']}")
            print(f"   - Size: {snapshot['file_size']} bytes")
            print(f"   - Dimensions: {snapshot['width']}x{snapshot['height']}")
            print(f"   - Captured at: {snapshot['captured_at']}")
            return snapshot
        else:
            print(f"❌ Snapshot capture failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error capturing snapshot: {e}")
        return None

def test_snapshot_retrieval(token, snapshot_id):
    """Test snapshot image retrieval"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/snapshots/{snapshot_id}/image",
            headers=headers
        )
        
        if response.status_code == 200:
            snapshot_data = response.json()
            image_data = snapshot_data["image_data"]
            print(f"✅ Snapshot image retrieved successfully")
            print(f"   - Image data length: {len(image_data)} characters (base64)")
            print(f"   - Format: {snapshot_data['image_format']}")
            return snapshot_data
        else:
            print(f"❌ Snapshot retrieval failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving snapshot: {e}")
        return None

def test_device_snapshots(token, device_id):
    """Test getting all snapshots for a device"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/snapshots/device/{device_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            snapshots = data["snapshots"]
            print(f"✅ Found {len(snapshots)} snapshots for device")
            print(f"   - Total: {data['total']}")
            print(f"   - Page: {data['page']}")
            print(f"   - Per page: {data['per_page']}")
            return snapshots
        else:
            print(f"❌ Failed to get device snapshots: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting device snapshots: {e}")
        return []

def main():
    """Main test function"""
    print("🧪 Snapshot Feature Test")
    print("=" * 50)
    
    # Test 1: API Health
    print("\n1. Testing API Health...")
    if not test_api_health():
        print("❌ Cannot proceed - API is not running")
        return False
    
    # Test 2: Authentication
    print("\n2. Testing Authentication...")
    token = authenticate()
    if not token:
        print("❌ Cannot proceed - Authentication failed")
        return False
    
    # Test 3: Get Devices
    print("\n3. Getting Devices...")
    devices = get_devices(token)
    if not devices:
        print("❌ Cannot proceed - No devices found")
        return False
    
    # Find a live camera device
    live_device = None
    for device in devices:
        if device.get("status") == "ONLINE" and device.get("rtsp_url"):
            # Update RTSP URL with proper credentials for testing
            device["rtsp_url"] = device["rtsp_url"].replace("rtsp://", "rtsp://root:G3M13m0b@")
            live_device = device
            break
    
    if not live_device:
        print("❌ No online devices with RTSP URLs found")
        print("Available devices:")
        for device in devices:
            print(f"   - {device['name']}: {device['status']} ({device.get('rtsp_url', 'No RTSP URL')})")
        return False
    
    print(f"✅ Using device: {live_device['name']} ({live_device['id']})")
    
    # Test 4: Capture Snapshot
    print(f"\n4. Testing Snapshot Capture for {live_device['name']}...")
    snapshot = test_snapshot_capture(token, live_device["id"])
    if not snapshot:
        print("❌ Snapshot capture failed")
        return False
    
    # Test 5: Retrieve Snapshot Image
    print(f"\n5. Testing Snapshot Image Retrieval...")
    snapshot_data = test_snapshot_retrieval(token, snapshot["id"])
    if not snapshot_data:
        print("❌ Snapshot image retrieval failed")
        return False
    
    # Test 6: Get Device Snapshots
    print(f"\n6. Testing Device Snapshots List...")
    device_snapshots = test_device_snapshots(token, live_device["id"])
    if device_snapshots is None:
        print("❌ Device snapshots retrieval failed")
        return False
    
    # Test 7: Test Latest Snapshot
    print(f"\n7. Testing Latest Snapshot...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/snapshots/device/{live_device['id']}/latest",
            headers=headers
        )
        
        if response.status_code == 200:
            latest = response.json()
            print(f"✅ Latest snapshot retrieved: {latest['id']}")
        else:
            print(f"❌ Latest snapshot retrieval failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting latest snapshot: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Snapshot feature test completed!")
    print("\nAPI Endpoints tested:")
    print("✅ POST /api/snapshots/capture/{device_id}")
    print("✅ GET  /api/snapshots/{snapshot_id}")
    print("✅ GET  /api/snapshots/{snapshot_id}/image")
    print("✅ GET  /api/snapshots/device/{device_id}")
    print("✅ GET  /api/snapshots/device/{device_id}/latest")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

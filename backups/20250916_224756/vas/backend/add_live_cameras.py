#!/usr/bin/env python3
"""
Live Camera Addition Script for VAS Phase 1
This script adds the live cameras from .env file to the system.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional

# API Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class VASDeviceManager:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """Login and get authentication token"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login-json",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Login successful for user: {username}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def add_device(self, device_data: Dict) -> Optional[str]:
        """Add a device to the system"""
        try:
            response = self.session.post(
                f"{self.base_url}/devices/",
                json=device_data
            )
            if response.status_code == 201:
                data = response.json()
                device_id = data.get("id")
                print(f"✅ Device added successfully: {device_data['name']} (ID: {device_id})")
                return device_id
            else:
                print(f"❌ Failed to add device {device_data['name']}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error adding device {device_data['name']}: {e}")
            return None
    
    def validate_device(self, device_data: Dict) -> bool:
        """Validate an RTSP stream"""
        try:
            response = self.session.post(
                f"{self.base_url}/devices/validate",
                json=device_data
            )
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("is_valid", False)
                message = data.get("message", "Unknown")
                status = "✅ Valid" if is_valid else "❌ Invalid"
                print(f"{status} RTSP Stream: {device_data['name']} - {message}")
                return is_valid
            else:
                print(f"❌ Validation failed for {device_data['name']}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Validation error for {device_data['name']}: {e}")
            return False
    
    def list_devices(self) -> List[Dict]:
        """List all devices"""
        try:
            response = self.session.get(f"{self.base_url}/devices/")
            if response.status_code == 200:
                devices = response.json()
                print(f"📋 Found {len(devices)} devices in the system")
                return devices
            else:
                print(f"❌ Failed to list devices: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error listing devices: {e}")
            return []

def create_live_cameras() -> List[Dict]:
    """Create live camera configurations from environment variables"""
    cameras = []
    
    # Camera 1
    camera1_ip = os.getenv('CAMERA_1_IP', '172.16.16.122')
    camera1_rtsp = os.getenv('CAMERA_1_RTSP_URL', f"rtsp://root:G3M13m0b@{camera1_ip}:554/stream1")
    camera_username = os.getenv('CAMERA_USERNAME', 'root')
    camera_password = os.getenv('CAMERA_PASSWORD', 'G3M13m0b')
    
    cameras.append({
        "name": f"Live Camera 1 - {camera1_ip}",
        "device_type": "ip_camera",
        "manufacturer": "Unknown",
        "model": "Live Camera",
        "ip_address": camera1_ip,
        "port": 554,
        "rtsp_url": camera1_rtsp,
        "username": camera_username,
        "password": camera_password,
        "location": "Network Camera 1",
        "description": "Live test camera from network",
        "tags": ["live", "test", "network"],
        "metadata": {
            "resolution": "Unknown",
            "live": True,
            "test": True
        }
    })
    
    # Camera 2
    camera2_ip = os.getenv('CAMERA_2_IP', '172.16.16.123')
    camera2_rtsp = os.getenv('CAMERA_2_RTSP_URL', f"rtsp://root:G3M13m0b@{camera2_ip}:554/stream1")
    
    cameras.append({
        "name": f"Live Camera 2 - {camera2_ip}",
        "device_type": "ip_camera",
        "manufacturer": "Unknown",
        "model": "Live Camera",
        "ip_address": camera2_ip,
        "port": 554,
        "rtsp_url": camera2_rtsp,
        "username": camera_username,
        "password": camera_password,
        "location": "Network Camera 2",
        "description": "Live test camera from network",
        "tags": ["live", "test", "network"],
        "metadata": {
            "resolution": "Unknown",
            "live": True,
            "test": True
        }
    })
    
    return cameras

def main():
    """Main function to add live cameras"""
    print("🚀 VAS Phase 1 - Live Camera Addition")
    print("=" * 50)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment")
    
    # Initialize device manager
    manager = VASDeviceManager()
    
    # Login
    if not manager.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        print("❌ Cannot proceed without authentication")
        return
    
    # Get live cameras
    live_cameras = create_live_cameras()
    print(f"\n📋 Found {len(live_cameras)} live cameras to add")
    
    # Add cameras
    added_cameras = []
    for i, camera in enumerate(live_cameras, 1):
        print(f"\n{i}/{len(live_cameras)} Adding camera: {camera['name']}")
        print(f"   IP: {camera['ip_address']}")
        print(f"   RTSP: {camera['rtsp_url']}")
        
        device_id = manager.add_device(camera)
        if device_id:
            added_cameras.append(device_id)
        
        # Small delay to avoid overwhelming the API
        time.sleep(1)
    
    print(f"\n✅ Successfully added {len(added_cameras)} out of {len(live_cameras)} cameras")
    
    # List all devices
    print("\n📋 Current devices in system:")
    devices = manager.list_devices()
    for device in devices:
        print(f"  - {device['name']} ({device['device_type']}) - {device['location']}")
    
    # Test validation on live cameras
    print("\n🔍 Testing RTSP validation on live cameras:")
    for camera in live_cameras:
        manager.validate_device(camera)
        time.sleep(2)  # Longer delay for live camera validation
    
    print("\n🎉 Live camera addition completed!")
    print("\nNext steps:")
    print("1. Check the API endpoints to manage these cameras")
    print("2. Monitor camera status and health")
    print("3. Test RTSP stream validation")
    print("4. Integrate with your frontend application")

if __name__ == "__main__":
    main() 
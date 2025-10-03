#!/usr/bin/env python3
"""
Sample RTSP Device Addition Script for VAS Phase 1
This script demonstrates how to add various types of RTSP devices to the system.
"""

import requests
import json
import time
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

def create_sample_devices() -> List[Dict]:
    """Create sample device configurations"""
    return [
        # IP Camera - Hikvision
        {
            "name": "Hikvision IP Camera - Front Door",
            "device_type": "ip_camera",
            "manufacturer": "Hikvision",
            "model": "DS-2CD2142FWD-I",
            "ip_address": "192.168.1.100",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101",
            "username": "admin",
            "password": "password123",
            "location": "Front Door",
            "description": "Main entrance security camera",
            "tags": ["security", "entrance", "outdoor"],
            "metadata": {
                "resolution": "1080p",
                "night_vision": True,
                "motion_detection": True,
                "storage": "64GB SD card"
            }
        },
        
        # IP Camera - Dahua
        {
            "name": "Dahua IP Camera - Parking Lot",
            "device_type": "ip_camera",
            "manufacturer": "Dahua",
            "model": "IPC-HDW4431C-A",
            "ip_address": "192.168.1.101",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0",
            "username": "admin",
            "password": "password123",
            "location": "Parking Lot",
            "description": "Parking lot surveillance camera",
            "tags": ["security", "parking", "outdoor"],
            "metadata": {
                "resolution": "4MP",
                "night_vision": True,
                "ptz": False,
                "storage": "128GB SD card"
            }
        },
        
        # IP Camera - Axis
        {
            "name": "Axis IP Camera - Office Area",
            "device_type": "ip_camera",
            "manufacturer": "Axis",
            "model": "M1065-L",
            "ip_address": "192.168.1.102",
            "port": 554,
            "rtsp_url": "rtsp://root:password123@192.168.1.102:554/axis-media/media.amp",
            "username": "root",
            "password": "password123",
            "location": "Office Area",
            "description": "Indoor office monitoring camera",
            "tags": ["monitoring", "indoor", "office"],
            "metadata": {
                "resolution": "720p",
                "night_vision": False,
                "audio": True,
                "storage": "Network storage"
            }
        },
        
        # IP Camera - Foscam
        {
            "name": "Foscam IP Camera - Warehouse",
            "device_type": "ip_camera",
            "manufacturer": "Foscam",
            "model": "FI9900P",
            "ip_address": "192.168.1.103",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.103:554/videoMain",
            "username": "admin",
            "password": "password123",
            "location": "Warehouse",
            "description": "Warehouse security camera",
            "tags": ["security", "warehouse", "indoor"],
            "metadata": {
                "resolution": "1080p",
                "night_vision": True,
                "ptz": True,
                "storage": "32GB SD card"
            }
        },
        
        # IP Camera - Reolink
        {
            "name": "Reolink IP Camera - Backyard",
            "device_type": "ip_camera",
            "manufacturer": "Reolink",
            "model": "RLC-410",
            "ip_address": "192.168.1.104",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.104:554/h264Preview_01_main",
            "username": "admin",
            "password": "password123",
            "location": "Backyard",
            "description": "Backyard surveillance camera",
            "tags": ["security", "backyard", "outdoor"],
            "metadata": {
                "resolution": "4MP",
                "night_vision": True,
                "motion_detection": True,
                "storage": "128GB SD card"
            }
        },
        
        # DVR System
        {
            "name": "Hikvision DVR - Main System",
            "device_type": "dvr",
            "manufacturer": "Hikvision",
            "model": "DS-7204HVI-K1",
            "ip_address": "192.168.1.200",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.200:554/Streaming/Channels/101",
            "username": "admin",
            "password": "password123",
            "location": "Server Room",
            "description": "Main DVR system with 4 channels",
            "tags": ["dvr", "recording", "server"],
            "metadata": {
                "channels": 4,
                "storage": "2TB HDD",
                "resolution": "1080p",
                "backup": True
            }
        },
        
        # NVR System
        {
            "name": "Dahua NVR - Network System",
            "device_type": "nvr",
            "manufacturer": "Dahua",
            "model": "NVR4104-P-4KS2",
            "ip_address": "192.168.1.201",
            "port": 554,
            "rtsp_url": "rtsp://admin:password123@192.168.1.201:554/cam/realmonitor?channel=1&subtype=0",
            "username": "admin",
            "password": "password123",
            "location": "Network Operations Center",
            "description": "Network video recorder for IP cameras",
            "tags": ["nvr", "network", "recording"],
            "metadata": {
                "channels": 4,
                "storage": "4TB HDD",
                "resolution": "4K",
                "poe": True
            }
        },
        
        # Test Stream (Public)
        {
            "name": "Test Stream - Public RTSP",
            "device_type": "test_stream",
            "manufacturer": "Test",
            "model": "Public Stream",
            "ip_address": "demo.openrtsp.com",
            "port": 554,
            "rtsp_url": "rtsp://demo.openrtsp.com:554/live",
            "username": "",
            "password": "",
            "location": "Test Environment",
            "description": "Public test RTSP stream for validation",
            "tags": ["test", "public", "demo"],
            "metadata": {
                "resolution": "720p",
                "public": True,
                "test": True
            }
        }
    ]

def main():
    """Main function to add sample devices"""
    print("🚀 VAS Phase 1 - Sample Device Addition")
    print("=" * 50)
    
    # Initialize device manager
    manager = VASDeviceManager()
    
    # Login
    if not manager.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        print("❌ Cannot proceed without authentication")
        return
    
    # Get sample devices
    sample_devices = create_sample_devices()
    print(f"\n📋 Found {len(sample_devices)} sample devices to add")
    
    # Add devices
    added_devices = []
    for i, device in enumerate(sample_devices, 1):
        print(f"\n{i}/{len(sample_devices)} Adding device: {device['name']}")
        device_id = manager.add_device(device)
        if device_id:
            added_devices.append(device_id)
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    print(f"\n✅ Successfully added {len(added_devices)} out of {len(sample_devices)} devices")
    
    # List all devices
    print("\n📋 Current devices in system:")
    devices = manager.list_devices()
    for device in devices:
        print(f"  - {device['name']} ({device['device_type']}) - {device['location']}")
    
    # Test validation on a few devices
    print("\n🔍 Testing RTSP validation on sample devices:")
    test_devices = sample_devices[:3]  # Test first 3 devices
    for device in test_devices:
        manager.validate_device(device)
        time.sleep(1)  # Delay between validations
    
    print("\n🎉 Sample device addition completed!")
    print("\nNext steps:")
    print("1. Use the API endpoints to manage these devices")
    print("2. Run discovery to find more devices on your network")
    print("3. Validate RTSP streams for real devices")
    print("4. Monitor device status and health")

if __name__ == "__main__":
    main() 
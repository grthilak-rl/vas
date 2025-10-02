"""
Core Constants for VAS Application
This file contains shared constants like device definitions and mappings
to ensure consistency across different services.
"""

# Static mapping of device IDs to their corresponding Janus proxy mountpoint IDs
# This MUST be kept in sync with the configuration in janus/janus.plugin.streaming.jcfg
DEVICE_TO_MOUNTPOINT_MAP = {
    # Working cameras (have actual RTSP streams)
    "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c": 1,  # Live Camera 1 - Office
    "df5ec5a5-f3f2-4672-971b-b5df48fc9a05": 2,  # Live Camera 2 - Lobby
    
    # Dummy cameras (no actual RTSP streams - will show as inactive)
    "11061970-2d51-4e3c-a023-bf9f4a5280aa": 3,  # Axis IP Camera - Office Area
    "e3494343-e9bf-4fae-89b4-bf27e7c3b329": 4,  # Dahua IP Camera - Parking Lot
    "a7c106aa-7911-41ab-8e48-2f9babba6e95": 5,  # Dahua NVR - Network System
    "c7f310ad-edfd-4322-aadc-d395002324e8": 6,  # Foscam IP Camera - Warehouse
    "a69c578c-a07f-421b-b9f9-488bd3c97eab": 7,  # Hikvision DVR - Main System
    "0aafe11d-f5f8-4ebe-b07e-24836e96c87e": 8,  # Hikvision IP Camera - Front Door
    "944f7a53-7d95-4263-89b0-d67ab189aa15": 9,  # Reolink IP Camera - Backyard
    "e72de55e-1441-4daf-925b-e6285bad1675": 10, # Test Stream - Public RTSP
    
    # Legacy mappings (kept for compatibility)
    "739788de-c89f-41c2-b63e-a0f843af6b00": 1,  # Live Camera 1 (legacy)
    "407efe14-df4c-4aa1-aa45-cc6312695aee": 2,  # Live Camera 2 (legacy)
    "f00f00f0-f00f-f00f-f00f-f00f00f00f00": 3,  # Test Camera (legacy)
}

# Standard devices to populate in the database
STANDARD_DEVICES = [
    {
        "id": "739788de-c89f-41c2-b63e-a0f843af6b00",
        "name": "Live Camera 1",
        "device_type": "ip_camera",
        "manufacturer": "Generic",
        "model": "IP Camera",
        "ip_address": "172.16.16.122",
        "port": 554,
        "rtsp_url": "rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp",
        "username": "root",
        "password": "G3M13m0b",
        "location": "Location 1",
        "description": "Live Camera 1 - Network surveillance camera",
        "tags": ["surveillance", "live", "network"],
        "device_metadata": {"type": "ip_camera", "network": "internal"},
        "hostname": "camera1.local",
        "vendor": "Generic",
        "resolution": "1920x1080",
        "codec": "HEVC",
        "fps": 25
    },
    {
        "id": "407efe14-df4c-4aa1-aa45-cc6312695aee",
        "name": "Live Camera 2",
        "device_type": "ip_camera",
        "manufacturer": "Generic",
        "model": "IP Camera",
        "ip_address": "172.16.16.123",
        "port": 554,
        "rtsp_url": "rtsp://root:G3M13m0b@172.16.16.123/live1s1.sdp",
        "username": "root",
        "password": "G3M13m0b",
        "location": "Location 2",
        "description": "Live Camera 2 - Network surveillance camera",
        "tags": ["surveillance", "live", "network"],
        "device_metadata": {"type": "ip_camera", "network": "internal"},
        "hostname": "camera2.local",
        "vendor": "Generic",
        "resolution": "2688x1520",
        "codec": "HEVC",
        "fps": 30
    },
    {
        "id": "f00f00f0-f00f-f00f-f00f-f00f00f00f00",
        "name": "Test Camera",
        "device_type": "ip_camera",
        "manufacturer": "Test",
        "model": "Test Camera",
        "ip_address": "192.168.1.100",
        "port": 554,
        "rtsp_url": "rtsp://192.168.1.100:554/stream",
        "username": "admin",
        "password": "admin123",
        "location": "Test Location",
        "description": "Test Camera for development",
        "tags": ["test", "development"],
        "device_metadata": {"type": "test_camera", "network": "test"},
        "hostname": "testcamera.local",
        "vendor": "Test",
        "resolution": "1280x720",
        "codec": "H.264",
        "fps": 25
    }
] 
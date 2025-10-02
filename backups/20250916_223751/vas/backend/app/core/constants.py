"""
Core Constants for VAS Application
This file contains shared constants like device definitions and mappings
to ensure consistency across different services.
"""

# Static mapping of device IDs to their corresponding Janus proxy mountpoint IDs
# This MUST be kept in sync with the configuration in janus/janus.plugin.streaming.jcfg
DEVICE_TO_MOUNTPOINT_MAP = {
    "739788de-c89f-41c2-b63e-a0f843af6b00": 10001,  # Live Camera 1
    "407efe14-df4c-4aa1-aa45-cc6312695aee": 10002,  # Live Camera 2
    "f00f00f0-f00f-f00f-f00f-f00f00f00f00": 10003,  # Test Camera
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
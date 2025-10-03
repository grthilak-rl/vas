# VAS Phase 1 - API Usage Guide

## Quick Start

### 1. Authentication
First, get an authentication token:

```bash
curl -X POST "http://localhost:8000/api/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 2. Add a Sample RTSP Device

```bash
curl -X POST "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test IP Camera",
    "device_type": "ip_camera",
    "manufacturer": "Hikvision",
    "model": "DS-2CD2142FWD-I",
    "ip_address": "192.168.1.100",
    "port": 554,
    "rtsp_url": "rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101",
    "username": "admin",
    "password": "password123",
    "location": "Front Door",
    "description": "Test security camera",
    "tags": ["security", "test"],
    "metadata": {
      "resolution": "1080p",
      "night_vision": true
    }
  }'
```

### 3. List All Devices

```bash
curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Validate RTSP Stream

```bash
curl -X POST "http://localhost:8000/api/devices/validate" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "rtsp_url": "rtsp://demo.openrtsp.com:554/live",
    "username": "",
    "password": ""
  }'
```

### 5. Start Device Discovery

```bash
curl -X POST "http://localhost:8000/api/discover/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "network_range": "192.168.1.0/24",
    "scan_ports": [554, 80, 443],
    "timeout": 30
  }'
```

## Device Types Supported

### 1. IP Camera
```json
{
  "name": "IP Camera Example",
  "device_type": "ip_camera",
  "manufacturer": "Hikvision",
  "model": "DS-2CD2142FWD-I",
  "ip_address": "192.168.1.100",
  "port": 554,
  "rtsp_url": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
  "username": "admin",
  "password": "password",
  "location": "Location Name",
  "description": "Camera description",
  "tags": ["security", "outdoor"],
  "metadata": {
    "resolution": "1080p",
    "night_vision": true,
    "ptz": false
  }
}
```

### 2. DVR (Digital Video Recorder)
```json
{
  "name": "DVR System",
  "device_type": "dvr",
  "manufacturer": "Hikvision",
  "model": "DS-7204HVI-K1",
  "ip_address": "192.168.1.200",
  "port": 554,
  "rtsp_url": "rtsp://admin:password@192.168.1.200:554/Streaming/Channels/101",
  "username": "admin",
  "password": "password",
  "location": "Server Room",
  "description": "DVR system with multiple channels",
  "tags": ["dvr", "recording"],
  "metadata": {
    "channels": 4,
    "storage": "2TB HDD",
    "backup": true
  }
}
```

### 3. NVR (Network Video Recorder)
```json
{
  "name": "NVR System",
  "device_type": "nvr",
  "manufacturer": "Dahua",
  "model": "NVR4104-P-4KS2",
  "ip_address": "192.168.1.201",
  "port": 554,
  "rtsp_url": "rtsp://admin:password@192.168.1.201:554/cam/realmonitor?channel=1&subtype=0",
  "username": "admin",
  "password": "password",
  "location": "NOC",
  "description": "Network video recorder",
  "tags": ["nvr", "network"],
  "metadata": {
    "channels": 4,
    "storage": "4TB HDD",
    "poe": true
  }
}
```

## Common RTSP URL Formats

### Hikvision
- `rtsp://username:password@ip:554/Streaming/Channels/101` (Main stream)
- `rtsp://username:password@ip:554/Streaming/Channels/102` (Sub stream)

### Dahua
- `rtsp://username:password@ip:554/cam/realmonitor?channel=1&subtype=0` (Main stream)
- `rtsp://username:password@ip:554/cam/realmonitor?channel=1&subtype=1` (Sub stream)

### Axis
- `rtsp://username:password@ip:554/axis-media/media.amp`

### Foscam
- `rtsp://username:password@ip:554/videoMain`

### Reolink
- `rtsp://username:password@ip:554/h264Preview_01_main`

## API Endpoints Reference

### Authentication
- `POST /api/auth/login-json` - Login and get token

### Devices
- `GET /api/devices/` - List all devices
- `POST /api/devices/` - Add new device
- `GET /api/devices/{device_id}` - Get device details
- `PUT /api/devices/{device_id}` - Update device
- `DELETE /api/devices/{device_id}` - Delete device
- `POST /api/devices/validate` - Validate RTSP stream

### Discovery
- `POST /api/discover/` - Start device discovery
- `GET /api/discover/` - List discovery tasks
- `GET /api/discover/{task_id}` - Get discovery task status

### Health
- `GET /api/health` - Health check

## Python Examples

### Using requests library
```python
import requests

# Login
response = requests.post("http://localhost:8000/api/auth/login-json", 
                        json={"username": "admin", "password": "admin123"})
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Add device
device_data = {
    "name": "Test Camera",
    "device_type": "ip_camera",
    "manufacturer": "Hikvision",
    "model": "DS-2CD2142FWD-I",
    "ip_address": "192.168.1.100",
    "port": 554,
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
    "username": "admin",
    "password": "password",
    "location": "Test Location",
    "description": "Test camera",
    "tags": ["test"],
    "metadata": {"resolution": "1080p"}
}

response = requests.post("http://localhost:8000/api/devices/", 
                        json=device_data, headers=headers)
print(response.json())
```

## Error Handling

Common error responses:

- `401 Unauthorized` - Invalid or missing authentication token
- `403 Forbidden` - Insufficient permissions
- `422 Validation Error` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Security Notes

1. Always use HTTPS in production
2. Store passwords securely (they are encrypted in the database)
3. Use strong authentication tokens
4. Regularly rotate credentials
5. Monitor API access logs

## Testing with Public Streams

For testing without real devices, you can use public RTSP streams:

```json
{
  "rtsp_url": "rtsp://demo.openrtsp.com:554/live",
  "username": "",
  "password": ""
}
```

## Next Steps

1. Run the sample device script: `python3 add_sample_devices.py`
2. Test with real RTSP devices on your network
3. Use the discovery feature to find devices automatically
4. Monitor device health and status
5. Integrate with your frontend application 
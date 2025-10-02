# Snapshot Feature Documentation

## Overview

The VAS (Video Analytics System) now includes a snapshot feature that allows capturing still images from camera RTSP feeds and storing them in the database. This feature is designed to work alongside the existing WebRTC streaming functionality without affecting performance.

## Features

- **On-demand snapshot capture** from RTSP camera feeds
- **Database storage** of snapshot images with metadata
- **RESTful API** for snapshot management
- **Base64 image retrieval** for easy integration with 3rd party applications
- **Device-specific snapshot history** with pagination
- **No impact on existing WebRTC streaming** performance

## API Endpoints

### 1. Capture Snapshot
```http
POST /api/snapshots/capture/{device_id}
```

Captures a snapshot from the specified device's RTSP feed.

**Response:**
```json
{
  "id": "d1dec4ef-4be6-4fdd-81c5-df100fde82e7",
  "device_id": "83634046-7a20-41be-a420-02b3c6173ee6",
  "image_format": "jpeg",
  "width": 1920,
  "height": 1080,
  "file_size": 252901,
  "captured_at": "2025-10-02T12:53:57.558091",
  "created_at": "2025-10-02T12:53:57.558091",
  "updated_at": "2025-10-02T12:53:57.558091"
}
```

### 2. Get Snapshot Image (Base64)
```http
GET /api/snapshots/{snapshot_id}/image
```

Retrieves the snapshot image as a Base64 encoded string.

**Response:**
```json
{
  "id": "d1dec4ef-4be6-4fdd-81c5-df100fde82e7",
  "device_id": "83634046-7a20-41be-a420-02b3c6173ee6",
  "image_data": "base64_encoded_image_data...",
  "image_format": "jpeg",
  "width": 1920,
  "height": 1080,
  "file_size": 252901,
  "captured_at": "2025-10-02T12:53:57.558091"
}
```

### 3. Get Snapshot Image (Binary)
```http
GET /api/snapshots/{snapshot_id}/binary
```

Retrieves the raw image data with appropriate Content-Type header.

**Response:** Binary image data with `Content-Type: image/jpeg`

### 4. List Device Snapshots
```http
GET /api/snapshots/device/{device_id}?page=1&per_page=10
```

Lists all snapshots for a specific device with pagination.

**Response:**
```json
{
  "snapshots": [
    {
      "id": "d1dec4ef-4be6-4fdd-81c5-df100fde82e7",
      "device_id": "83634046-7a20-41be-a420-02b3c6173ee6",
      "image_format": "jpeg",
      "width": 1920,
      "height": 1080,
      "file_size": 252901,
      "captured_at": "2025-10-02T12:53:57.558091",
      "created_at": "2025-10-02T12:53:57.558091",
      "updated_at": "2025-10-02T12:53:57.558091"
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 10
}
```

### 5. Get Latest Snapshot
```http
GET /api/snapshots/device/{device_id}/latest
```

Retrieves the most recent snapshot for a device.

**Response:** Same as individual snapshot response

### 6. Delete Snapshot
```http
DELETE /api/snapshots/{snapshot_id}
```

Deletes a specific snapshot from the database.

**Response:**
```json
{
  "message": "Snapshot deleted successfully"
}
```

## Database Schema

### Snapshots Table
```sql
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    image_data BYTEA NOT NULL,
    image_format VARCHAR(10) NOT NULL DEFAULT 'jpeg',
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_snapshots_device_id ON snapshots(device_id);
```

## Technical Implementation

### Components

1. **Database Migration**: `003_add_snapshots_table.py`
2. **ORM Model**: `Snapshot` class in `models.py`
3. **Pydantic Schemas**: Snapshot request/response schemas in `schemas.py`
4. **Service Layer**: `SnapshotService` in `services/snapshot_service.py`
5. **API Router**: `snapshots.py` with FastAPI endpoints
6. **FFmpeg Integration**: Uses FFmpeg for RTSP stream capture

### FFmpeg Command
```bash
ffmpeg -rtsp_transport tcp -i {rtsp_url} -vframes 1 -q:v 2 -f image2 -y {output_path}
```

### Dependencies
- **FFmpeg**: For RTSP stream capture
- **Pillow**: For image processing and validation
- **PostgreSQL**: For snapshot storage

## Usage Examples

### Python Client
```python
import requests
import base64

# Authenticate
auth_response = requests.post(
    "http://localhost:8000/api/auth/login-json",
    json={"username": "admin", "password": "admin123"}
)
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Capture snapshot
snapshot_response = requests.post(
    f"http://localhost:8000/api/snapshots/capture/{device_id}",
    headers=headers
)
snapshot = snapshot_response.json()

# Get image data
image_response = requests.get(
    f"http://localhost:8000/api/snapshots/{snapshot['id']}/image",
    headers=headers
)
image_data = image_response.json()["image_data"]

# Decode and save image
with open("snapshot.jpg", "wb") as f:
    f.write(base64.b64decode(image_data))
```

### JavaScript/Node.js Client
```javascript
const axios = require('axios');
const fs = require('fs');

// Authenticate
const authResponse = await axios.post('http://localhost:8000/api/auth/login-json', {
    username: 'admin',
    password: 'admin123'
});
const token = authResponse.data.access_token;

// Capture snapshot
const snapshotResponse = await axios.post(
    `http://localhost:8000/api/snapshots/capture/${deviceId}`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
);

// Get image data
const imageResponse = await axios.get(
    `http://localhost:8000/api/snapshots/${snapshotResponse.data.id}/image`,
    { headers: { Authorization: `Bearer ${token}` } }
);

// Save image
const imageBuffer = Buffer.from(imageResponse.data.image_data, 'base64');
fs.writeFileSync('snapshot.jpg', imageBuffer);
```

## Performance Considerations

- **On-demand capture**: Snapshots are only taken when requested
- **Single frame capture**: FFmpeg captures only one frame per request
- **No impact on streaming**: Separate from WebRTC streaming pipeline
- **Database storage**: Images stored as binary data in PostgreSQL
- **Pagination support**: Large snapshot histories can be paginated

## Error Handling

### Common Error Responses

**Device not found:**
```json
{
  "error": "Device not found",
  "timestamp": "2025-10-02T12:53:57.558091",
  "path": "/api/snapshots/capture/invalid-device-id"
}
```

**Device offline:**
```json
{
  "error": "Device is not online. Current status: OFFLINE",
  "timestamp": "2025-10-02T12:53:57.558091",
  "path": "/api/snapshots/capture/device-id"
}
```

**RTSP stream error:**
```json
{
  "error": "Failed to capture snapshot. Check device connectivity and RTSP stream.",
  "timestamp": "2025-10-02T12:53:57.558091",
  "path": "/api/snapshots/capture/device-id"
}
```

## Security

- **Authentication required**: All endpoints require valid JWT token
- **Device ownership**: Users can only access snapshots for devices they have access to
- **Input validation**: All inputs are validated using Pydantic schemas
- **SQL injection protection**: Using SQLAlchemy ORM with parameterized queries

## Monitoring and Logging

- **FFmpeg logs**: Captured and logged for debugging
- **Database operations**: All database operations are logged
- **API requests**: All API requests are logged with timestamps
- **Error tracking**: Comprehensive error logging with stack traces

## Future Enhancements

- **Batch snapshot capture**: Capture snapshots from multiple devices
- **Scheduled snapshots**: Automatic snapshot capture at intervals
- **Image compression**: Configurable image quality and compression
- **Cloud storage**: Option to store snapshots in cloud storage
- **Image analysis**: Integration with AI/ML for image analysis
- **Webhook notifications**: Notify external systems when snapshots are captured

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed in the container
2. **RTSP authentication failed**: Check device credentials
3. **Database connection error**: Verify PostgreSQL is running
4. **Memory issues**: Large images may cause memory issues

### Debug Commands

```bash
# Check FFmpeg installation
docker-compose exec vas-backend ffmpeg -version

# Check database connection
docker-compose exec vas-backend python -c "from app.database import get_db; print('DB OK')"

# View logs
docker-compose logs -f vas-backend

# Test RTSP stream
docker-compose exec vas-backend ffmpeg -rtsp_transport tcp -i "rtsp://user:pass@ip/stream" -vframes 1 -f image2 -y test.jpg
```

## Version History

- **v1.0.0** (2025-10-02): Initial implementation
  - Basic snapshot capture functionality
  - Database storage with metadata
  - RESTful API endpoints
  - Base64 image retrieval
  - Device-specific snapshot management

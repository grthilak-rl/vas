# VAS Snapshot API Documentation

## Overview

The VAS Snapshot API provides endpoints for capturing, retrieving, and managing snapshots from camera feeds. This API is designed for 3rd party applications to integrate snapshot functionality into their systems.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require authentication using Bearer token:

```http
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Capture Snapshot

Capture a snapshot from a specific device's RTSP stream.

**Endpoint:** `POST /snapshots/capture/{device_id}`

**Parameters:**
- `device_id` (path): UUID of the device to capture snapshot from

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c",
  "image_format": "jpeg",
  "width": 1920,
  "height": 1080,
  "file_size": 245760,
  "captured_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Device not found
- `400 Bad Request`: Device is not online
- `500 Internal Server Error`: Failed to capture snapshot

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/snapshots/capture/05a9a734-f76d-4f45-9b0e-1e9c89b43e2c" \
  -H "Authorization: Bearer <your_token>"
```

### 2. Get Snapshot Metadata

Retrieve metadata for a specific snapshot.

**Endpoint:** `GET /snapshots/{snapshot_id}`

**Parameters:**
- `snapshot_id` (path): UUID of the snapshot

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c",
  "image_format": "jpeg",
  "width": 1920,
  "height": 1080,
  "file_size": 245760,
  "captured_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/snapshots/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <your_token>"
```

### 3. Get Snapshot Image (Base64)

Retrieve the snapshot image as Base64 encoded string.

**Endpoint:** `GET /snapshots/{snapshot_id}/image`

**Parameters:**
- `snapshot_id` (path): UUID of the snapshot

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c",
  "image_data": "iVBORw0KGgoAAAANSUhEUgAA...",
  "image_format": "jpeg",
  "width": 1920,
  "height": 1080,
  "file_size": 245760,
  "captured_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/snapshots/550e8400-e29b-41d4-a716-446655440000/image" \
  -H "Authorization: Bearer <your_token>"
```

### 4. Get Snapshot Image (Binary)

Retrieve the snapshot image as raw binary data.

**Endpoint:** `GET /snapshots/{snapshot_id}/binary`

**Parameters:**
- `snapshot_id` (path): UUID of the snapshot

**Response:**
- Content-Type: `image/jpeg` (or appropriate format)
- Body: Raw binary image data

**Example:**
```bash
curl "http://localhost:8000/api/v1/snapshots/550e8400-e29b-41d4-a716-446655440000/binary" \
  -H "Authorization: Bearer <your_token>" \
  -o snapshot.jpg
```

### 5. List Snapshots

Retrieve a paginated list of snapshots with optional device filtering.

**Endpoint:** `GET /snapshots`

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "snapshots": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "device_id": "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c",
      "image_format": "jpeg",
      "width": 1920,
      "height": 1080,
      "file_size": 245760,
      "captured_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 10
}
```

**Examples:**
```bash
# Get all snapshots
curl "http://localhost:8000/api/v1/snapshots" \
  -H "Authorization: Bearer <your_token>"

# Get snapshots for specific device
curl "http://localhost:8000/api/v1/snapshots?device_id=05a9a734-f76d-4f45-9b0e-1e9c89b43e2c" \
  -H "Authorization: Bearer <your_token>"

# Get snapshots with pagination
curl "http://localhost:8000/api/v1/snapshots?page=2&per_page=20" \
  -H "Authorization: Bearer <your_token>"
```

### 6. Delete Snapshot

Delete a specific snapshot.

**Endpoint:** `DELETE /snapshots/{snapshot_id}`

**Parameters:**
- `snapshot_id` (path): UUID of the snapshot to delete

**Response:**
```json
{
  "message": "Snapshot deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/snapshots/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <your_token>"
```

## Data Models

### SnapshotResponse
```json
{
  "id": "string (UUID)",
  "device_id": "string (UUID)",
  "image_format": "string (jpeg, png, etc.)",
  "width": "integer (optional)",
  "height": "integer (optional)",
  "file_size": "integer (optional)",
  "captured_at": "string (ISO 8601 datetime, optional)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

### SnapshotImageResponse
```json
{
  "id": "string (UUID)",
  "device_id": "string (UUID)",
  "image_data": "string (Base64 encoded)",
  "image_format": "string",
  "width": "integer (optional)",
  "height": "integer (optional)",
  "file_size": "integer (optional)",
  "captured_at": "string (ISO 8601 datetime, optional)"
}
```

### SnapshotListResponse
```json
{
  "snapshots": "array of SnapshotResponse",
  "total": "integer",
  "page": "integer",
  "per_page": "integer"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Device is not online. Current status: offline"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Device not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to capture snapshot. Check device connectivity and RTSP stream."
}
```

## Usage Examples

### Python Example
```python
import requests
import base64
from PIL import Image
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Capture snapshot
device_id = "05a9a734-f76d-4f45-9b0e-1e9c89b43e2c"
response = requests.post(f"{BASE_URL}/snapshots/capture/{device_id}", headers=HEADERS)
snapshot = response.json()

# Get image data
image_response = requests.get(f"{BASE_URL}/snapshots/{snapshot['id']}/image", headers=HEADERS)
image_data = image_response.json()

# Decode and save image
image_bytes = base64.b64decode(image_data['image_data'])
image = Image.open(BytesIO(image_bytes))
image.save(f"snapshot_{snapshot['id']}.jpg")
```

### JavaScript Example
```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token';

// Capture snapshot
async function captureSnapshot(deviceId) {
  const response = await fetch(`${BASE_URL}/snapshots/capture/${deviceId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Get image data
async function getSnapshotImage(snapshotId) {
  const response = await fetch(`${BASE_URL}/snapshots/${snapshotId}/image`, {
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Usage
captureSnapshot('05a9a734-f76d-4f45-9b0e-1e9c89b43e2c')
  .then(snapshot => {
    console.log('Snapshot captured:', snapshot);
    return getSnapshotImage(snapshot.id);
  })
  .then(imageData => {
    console.log('Image data received');
    // Use imageData.image_data (Base64) as needed
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## Rate Limiting

- Snapshot capture: 10 requests per minute per device
- Image retrieval: 100 requests per minute per user
- List operations: 50 requests per minute per user

## Best Practices

1. **Use Binary Endpoint**: For better performance, use the `/binary` endpoint instead of Base64 when possible
2. **Implement Caching**: Cache snapshot metadata to reduce API calls
3. **Handle Errors**: Always implement proper error handling for network issues
4. **Respect Rate Limits**: Implement exponential backoff for rate limit errors
5. **Clean Up**: Delete old snapshots to manage storage space

## Support

For API support and questions, please contact the VAS development team.

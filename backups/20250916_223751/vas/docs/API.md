# VAS Phase 1 API Documentation

## Overview

The Video Aggregation Service (VAS) Phase 1 API provides endpoints for discovering, validating, and managing RTSP-capable video devices across enterprise networks.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Login

**POST** `/api/auth/login-json`

Get a JWT token by providing credentials.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "role": "admin",
    "full_name": "Administrator"
  }
}
```

## Device Discovery

### Start Network Discovery

**POST** `/api/discover`

Start scanning subnets for RTSP-capable devices.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "subnets": ["192.168.1.0/24", "10.0.0.0/16"]
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Discovery started",
  "subnets": ["192.168.1.0/24", "10.0.0.0/16"],
  "estimated_duration": 45
}
```

### Get Discovery Status

**GET** `/api/discover/{task_id}`

Check the status of a discovery task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "subnets": ["192.168.1.0/24"],
  "results": {
    "192.168.1.0/24": [
      {
        "ip_address": "192.168.1.100",
        "hostname": "camera-01.local",
        "vendor": "Hikvision",
        "rtsp_url": "rtsp://192.168.1.100:554/h264Preview_01_main",
        "rtsp_ports": [554],
        "discovered_at": 1640995200.0
      }
    ]
  }
}
```

## Device Management

### List Devices

**GET** `/api/devices`

Get a paginated list of discovered devices.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Number of records to return (default: 100, max: 1000)
- `status_filter` (string): Filter by device status (ONLINE/OFFLINE/UNREACHABLE)
- `vendor_filter` (string): Filter by vendor name

**Response:**
```json
{
  "devices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "ip_address": "192.168.1.100",
      "hostname": "camera-01.local",
      "vendor": "Hikvision",
      "model": "DS-2CD2385G1-I",
      "rtsp_url": "rtsp://192.168.1.100:554/h264Preview_01_main",
      "resolution": "1920x1080",
      "codec": "h264",
      "fps": 25,
      "status": "ONLINE",
      "last_seen": "2023-12-01T10:00:00Z",
      "created_at": "2023-12-01T09:00:00Z",
      "updated_at": "2023-12-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 100
}
```

### Get Device Details

**GET** `/api/devices/{device_id}`

Get detailed information about a specific device.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "ip_address": "192.168.1.100",
  "hostname": "camera-01.local",
  "vendor": "Hikvision",
  "model": "DS-2CD2385G1-I",
  "rtsp_url": "rtsp://192.168.1.100:554/h264Preview_01_main",
  "resolution": "1920x1080",
  "codec": "h264",
  "fps": 25,
  "status": "ONLINE",
  "last_seen": "2023-12-01T10:00:00Z",
  "created_at": "2023-12-01T09:00:00Z",
  "updated_at": "2023-12-01T10:00:00Z"
}
```

### Update Device

**PATCH** `/api/devices/{device_id}`

Update device metadata.

**Request Body:**
```json
{
  "hostname": "camera-01-updated.local",
  "vendor": "Hikvision",
  "model": "DS-2CD2385G1-I",
  "rtsp_url": "rtsp://192.168.1.100:554/h264Preview_01_main"
}
```

### Delete Device

**DELETE** `/api/devices/{device_id}`

Remove a device from the database.

**Response:**
```json
{
  "message": "Device deleted successfully"
}
```

## RTSP Validation

### Validate Device

**POST** `/api/devices/validate`

Validate RTSP stream for a device.

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "username": "admin",
  "password": "password123",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1"
}
```

**Response:**
```json
{
  "ip_address": "192.168.1.100",
  "is_valid": true,
  "rtsp_url": "rtsp://192.168.1.100:554/h264Preview_01_main",
  "resolution": "1920x1080",
  "codec": "h264",
  "fps": 25,
  "error_message": null
}
```

### Get Device Status

**GET** `/api/devices/{device_id}/status`

Check current health status of a device.

**Response:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "ONLINE",
  "error": null,
  "last_checked": "2023-12-01T10:00:00Z"
}
```

## Health Check

### Service Health

**GET** `/api/health`

Check the health status of the service and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "ffprobe": "available"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "detail": "Additional error details",
  "timestamp": "2023-12-01T10:00:00Z",
  "path": "/api/devices"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

The API implements rate limiting:
- 10 requests per second per IP address
- Burst allowance of 20 requests

## Examples

### Complete Workflow

1. **Login to get token:**
```bash
curl -X POST "http://localhost:8000/api/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

2. **Start discovery:**
```bash
curl -X POST "http://localhost:8000/api/discover" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"subnets": ["192.168.1.0/24"]}'
```

3. **List discovered devices:**
```bash
curl -X GET "http://localhost:8000/api/devices" \
  -H "Authorization: Bearer <token>"
```

4. **Validate a device:**
```bash
curl -X POST "http://localhost:8000/api/devices/validate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.1.100"}'
```

## Interactive Documentation

Visit the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 
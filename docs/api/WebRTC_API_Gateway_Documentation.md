# WebRTC API Gateway Documentation

## Overview

The WebRTC API Gateway provides a RESTful interface for third-party applications to discover, connect to, and monitor video streams from the VAS (Video Aggregation Service) system. This API enables external applications to consume WebRTC video feeds without needing direct access to the underlying Janus Gateway.

## Base URL

```
http://10.30.250.245:8000/api/streams/webrtc
```

## Authentication

All endpoints require Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

### Getting an Authentication Token

```bash
curl -X POST "http://10.30.250.245:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## API Endpoints

### 1. List All WebRTC Streams

**Endpoint:** `GET /streams`

**Description:** Retrieve a list of all available WebRTC streams for third-party consumption.

**Request:**
```bash
curl -X GET "http://10.30.250.245:8000/api/streams/webrtc/streams" \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "streams": [
    {
      "stream_id": "1",
      "name": "Edge Camera 1 - Office",
      "type": "rtsp",
      "status": "active",
      "metadata": "Unit-001 Camera 1 - Office/Entrance",
      "enabled": true,
      "webrtc_endpoint": "/api/streams/webrtc/streams/1/config"
    },
    {
      "stream_id": "2",
      "name": "Edge Camera 2 - Lobby",
      "type": "rtsp",
      "status": "active",
      "metadata": "Unit-001 Camera 2 - Lobby/Reception",
      "enabled": true,
      "webrtc_endpoint": "/api/streams/webrtc/streams/2/config"
    }
  ],
  "total_count": 2,
  "api_version": "1.0.0",
  "timestamp": "2025-09-16T20:02:56.658251"
}
```

### 2. Get Stream Information

**Endpoint:** `GET /streams/{stream_id}`

**Description:** Get detailed information about a specific WebRTC stream.

**Parameters:**
- `stream_id` (path): The unique identifier of the stream

**Request:**
```bash
curl -X GET "http://10.30.250.245:8000/api/streams/webrtc/streams/1" \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "stream_id": "1",
  "name": "Edge Camera 1 - Office",
  "type": "rtsp",
  "status": "active",
  "metadata": "Unit-001 Camera 1 - Office/Entrance",
  "enabled": true,
  "webrtc_config_endpoint": "/api/streams/webrtc/streams/1/config",
  "status_endpoint": "/api/streams/webrtc/streams/1/status",
  "last_updated": "2025-09-16T20:02:56.658251"
}
```

### 3. Get WebRTC Connection Configuration

**Endpoint:** `GET /streams/{stream_id}/config`

**Description:** Get WebRTC connection configuration for a specific stream. This is the most important endpoint for third-party applications as it provides all the necessary information to establish a WebRTC connection.

**Parameters:**
- `stream_id` (path): The unique identifier of the stream

**Request:**
```bash
curl -X GET "http://10.30.250.245:8000/api/streams/webrtc/streams/1/config" \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "janus_websocket_url": "ws://10.30.250.245:8188",
  "janus_http_url": "http://10.30.250.245:8088",
  "mountpoint_id": 1,
  "plugin": "janus.plugin.streaming",
  "connection_timeout": 30000,
  "ice_servers": [
    {
      "urls": "stun:stun.l.google.com:19302"
    },
    {
      "urls": "stun:stun1.l.google.com:19302"
    }
  ],
  "webrtc_options": {
    "trickle": true,
    "ice_tcp": false,
    "ice_lite": false
  },
  "stream_info": {
    "name": "Edge Camera 1 - Office",
    "type": "rtsp",
    "enabled": true
  }
}
```

### 4. Get Stream Status

**Endpoint:** `GET /streams/{stream_id}/status`

**Description:** Get real-time status of a WebRTC stream.

**Parameters:**
- `stream_id` (path): The unique identifier of the stream

**Request:**
```bash
curl -X GET "http://10.30.250.245:8000/api/streams/webrtc/streams/1/status" \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "stream_id": "1",
  "status": "active",
  "enabled": true,
  "janus_healthy": true,
  "webrtc_ready": true,
  "streaming": true,
  "timestamp": "2025-09-16T20:02:56.658251"
}
```

### 5. Get System Status

**Endpoint:** `GET /system/status`

**Description:** Get overall WebRTC system status for monitoring and health checks.

**Request:**
```bash
curl -X GET "http://10.30.250.245:8000/api/streams/webrtc/system/status" \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "system_status": "healthy",
  "janus_healthy": true,
  "total_streams": 6,
  "active_streams": 2,
  "inactive_streams": 4,
  "enabled_streams": 6,
  "disabled_streams": 0,
  "webrtc_gateway_ready": true,
  "timestamp": "2025-09-16T20:02:56.658251",
  "api_version": "1.0.0"
}
```

## Response Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 401  | Unauthorized (invalid or missing token) |
| 404  | Stream not found |
| 500  | Internal server error |

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "timestamp": "2025-09-16T20:02:56.658251",
  "path": "/api/streams/webrtc/streams/999"
}
```

## WebRTC Client Integration

### Using the Configuration

To connect to a WebRTC stream, use the configuration from the `/config` endpoint:

1. **Connect to Janus WebSocket** using `janus_websocket_url`
2. **Attach to the streaming plugin** (`janus.plugin.streaming`)
3. **Watch the mountpoint** using `mountpoint_id`
4. **Handle SDP offers/answers** for WebRTC negotiation
5. **Attach video tracks** to your video element

### Example JavaScript Integration

```javascript
// Get stream configuration
const config = await fetch('/api/streams/webrtc/streams/1/config', {
  headers: { 'Authorization': 'Bearer ' + token }
}).then(r => r.json());

// Connect to Janus
const janus = new Janus({
  server: config.janus_websocket_url,
  success: function() {
    janus.attach({
      plugin: config.plugin,
      success: function(pluginHandle) {
        pluginHandle.send({
          message: { request: "watch", id: config.mountpoint_id }
        });
      },
      onmessage: function(msg, jsep) {
        if (jsep) {
          pluginHandle.createAnswer({
            jsep: jsep,
            success: function(jsep) {
              pluginHandle.send({ 
                message: { request: "start" }, 
                jsep: jsep 
              });
            }
          });
        }
      },
      onremotetrack: function(track, mid, added) {
        if (added && track.kind === 'video') {
          const stream = new MediaStream([track]);
          videoElement.srcObject = stream;
          videoElement.play();
        }
      }
    });
  }
});
```

## Rate Limiting

Currently, no rate limiting is implemented. However, it's recommended to:
- Cache stream configurations
- Implement reasonable polling intervals for status checks
- Use WebSocket connections for real-time updates when available

## Security Considerations

1. **Authentication**: Always use valid Bearer tokens
2. **HTTPS**: Use HTTPS in production environments
3. **CORS**: Configure CORS appropriately for your domain
4. **Token Expiration**: Handle token expiration gracefully

## Monitoring and Health Checks

Use the `/system/status` endpoint for:
- **Health monitoring** of the WebRTC gateway
- **Stream availability** monitoring
- **System capacity** planning
- **Alerting** when streams become unavailable

## Support

For technical support or questions about the WebRTC API Gateway:
- Check the interactive documentation at `http://10.30.250.245:8000/docs`
- Review the OpenAPI specification at `http://10.30.250.245:8000/openapi.json`
- Monitor system logs for debugging information

---

**API Version:** 1.0.0  
**Last Updated:** September 16, 2025  
**Server:** VAS Edge Unit 001

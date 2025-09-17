# WebRTC API Gateway - Quick Reference

## 🔗 Base URL
```
http://10.30.250.245:8000/api/streams/webrtc
```

## 🔑 Authentication
```bash
# Get token
curl -X POST "http://10.30.250.245:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token
curl -H "Authorization: Bearer <token>" <endpoint>
```

## 📋 Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/streams` | List all available streams |
| `GET` | `/streams/{id}` | Get stream details |
| `GET` | `/streams/{id}/config` | Get WebRTC connection config |
| `GET` | `/streams/{id}/status` | Get stream status |
| `GET` | `/system/status` | Get system health |

## 🚀 Quick Start Examples

### 1. List All Streams
```bash
curl -H "Authorization: Bearer <token>" \
  "http://10.30.250.245:8000/api/streams/webrtc/streams"
```

### 2. Get Stream Config (Most Important!)
```bash
curl -H "Authorization: Bearer <token>" \
  "http://10.30.250.245:8000/api/streams/webrtc/streams/1/config"
```

### 3. Check System Health
```bash
curl -H "Authorization: Bearer <token>" \
  "http://10.30.250.245:8000/api/streams/webrtc/system/status"
```

## 📊 Response Examples

### Stream List Response
```json
{
  "streams": [
    {
      "stream_id": "1",
      "name": "Edge Camera 1 - Office",
      "status": "active",
      "webrtc_endpoint": "/api/streams/webrtc/streams/1/config"
    }
  ],
  "total_count": 1
}
```

### WebRTC Config Response
```json
{
  "janus_websocket_url": "ws://10.30.250.245:8188",
  "mountpoint_id": 1,
  "plugin": "janus.plugin.streaming",
  "ice_servers": [
    {"urls": "stun:stun.l.google.com:19302"}
  ]
}
```

## 🔧 WebRTC Client Integration

```javascript
// 1. Get config
const config = await fetch('/api/streams/webrtc/streams/1/config', {
  headers: { 'Authorization': 'Bearer ' + token }
}).then(r => r.json());

// 2. Connect to Janus
const janus = new Janus({
  server: config.janus_websocket_url,
  success: function() {
    janus.attach({
      plugin: config.plugin,
      success: function(pluginHandle) {
        // 3. Watch stream
        pluginHandle.send({
          message: { request: "watch", id: config.mountpoint_id }
        });
      },
      onremotetrack: function(track, mid, added) {
        // 4. Display video
        if (added && track.kind === 'video') {
          videoElement.srcObject = new MediaStream([track]);
          videoElement.play();
        }
      }
    });
  }
});
```

## 📚 Full Documentation
- **Complete Guide**: `WebRTC_API_Gateway_Documentation.md`
- **Interactive Docs**: `http://10.30.250.245:8000/docs`
- **OpenAPI Spec**: `http://10.30.250.245:8000/openapi.json`

## ⚡ Status Codes
- `200` - Success
- `401` - Unauthorized
- `404` - Stream not found
- `500` - Server error

---
*Quick Reference v1.0.0 - VAS Edge Unit 001*

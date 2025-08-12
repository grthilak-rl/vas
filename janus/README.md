# Janus Gateway API for VAS Integration

A FastAPI-based service that provides a RESTful API for managing IP camera streams via Janus WebRTC Gateway, designed for integration with Video Aggregation Service (VAS).

## 🏗️ Architecture

```
┌─────────────────┐    REST API      ┌──────────────────┐    WebRTC     ┌─────────────┐
│   VAS Portal    │ ←──────────────→ │  FastAPI Service │ ←──────────→ │   Browser   │
│  (Web App)      │                  │     (Port 3000)  │              │   Client    │
└─────────────────┘                  └──────────────────┘              └─────────────┘
                                             │
                                             │ Janus HTTP API
                                             ▼
                                      ┌──────────────────┐    RTSP       ┌─────────────┐
                                      │  Janus Gateway   │ ←──────────→ │ IP Cameras  │
                                      │   (Port 8088)    │              │  (Network)  │
                                      └──────────────────┘              └─────────────┘
```

## 🚀 Quick Start

### 1. Start the Services

```bash
# Build and start all services
docker-compose up --build

# Check service health
curl http://localhost:3000/health
```

### 2. Add a Camera

```bash
curl -X POST "http://localhost:3000/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "entrance_cam",
    "name": "Entrance Camera",
    "rtsp_url": "rtsp://172.16.16.122/live1s1.sdp",
    "username": "root",
    "password": "G3M13m0b",
    "auth_method": "digest",
    "description": "Main entrance monitoring"
  }'
```

### 3. View Stream in Browser

Navigate to `http://localhost/` to view the stream, or integrate with VAS using the provided JavaScript client.

## 📡 API Endpoints

### Camera Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/cameras` | Add a new camera |
| `GET` | `/cameras` | List all cameras |
| `GET` | `/cameras/{id}` | Get camera details |
| `GET` | `/cameras/{id}/stream` | Get WebRTC stream info |
| `POST` | `/cameras/{id}/restart` | Restart camera stream |
| `DELETE` | `/cameras/{id}` | Remove camera |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API documentation |

## 🔧 Configuration

### Environment Variables

- `JANUS_HTTP_URL`: Janus HTTP API URL (default: `http://localhost:8088/janus`)
- `JANUS_ADMIN_URL`: Janus Admin API URL (default: `http://localhost:7088/admin`)
- `JANUS_WS_URL`: Janus WebSocket URL (default: `ws://localhost:8188/janus`)

### Janus Configuration

The service automatically manages Janus streaming mountpoints via the Admin API. Key configuration files:

- `config/janus.jcfg`: Main Janus configuration
- `config/janus.plugin.streaming.jcfg`: Streaming plugin configuration
- `config/janus.transport.websockets.jcfg`: WebSocket transport
- `config/janus.transport.http.jcfg`: HTTP transport

## 🎯 VAS Integration

### JavaScript Client

```javascript
import { VASJanusClient } from './vas_integration.js';

const janusClient = new VASJanusClient('http://localhost:3000');

// Add a camera
await janusClient.addCamera({
    camera_id: 'cam001',
    name: 'Lobby Camera',
    rtsp_url: 'rtsp://camera.ip/stream',
    username: 'admin',
    password: 'password'
});

// Start streaming to video element
const videoElement = document.getElementById('video-player');
await janusClient.startCameraStream('cam001', videoElement);
```

### React/Vue Integration

```javascript
// React Hook example
function useCameraStream(cameraId) {
    const [streaming, setStreaming] = useState(false);
    const videoRef = useRef(null);
    const janusClient = useRef(new VASJanusClient('http://localhost:3000'));

    const startStream = async () => {
        try {
            await janusClient.current.startCameraStream(cameraId, videoRef.current);
            setStreaming(true);
        } catch (error) {
            console.error('Stream error:', error);
        }
    };

    const stopStream = async () => {
        await janusClient.current.stopCameraStream(cameraId);
        setStreaming(false);
    };

    return { videoRef, streaming, startStream, stopStream };
}
```

## 🐳 Docker Services

### Janus Gateway
- **Ports**: 8088 (HTTP), 8188 (WebSocket), 7088 (Admin), 20000-20010 (RTP)
- **Health Check**: `/janus/info` endpoint
- **Features**: RTSP streaming, WebRTC conversion, Digest authentication

### FastAPI Service
- **Port**: 3000
- **Health Check**: `/health` endpoint
- **Features**: Dynamic camera management, Janus API wrapper, CORS enabled

### Nginx Web Server
- **Port**: 80
- **Purpose**: Serve demo frontend and static assets

## 📊 Monitoring & Logging

### Health Checks

```bash
# Check all services
curl http://localhost:3000/health

# Check specific camera
curl http://localhost:3000/cameras/entrance_cam
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f janus-api
docker-compose logs -f janus
```

### Metrics

The FastAPI service provides metrics at `/health`:

```json
{
    "status": "healthy",
    "janus_connectivity": "ok",
    "active_cameras": 5,
    "active_sessions": 3
}
```

## 🔒 Production Considerations

### Security

1. **API Authentication**: Add JWT/OAuth2 authentication
2. **CORS**: Configure specific origins instead of `*`
3. **HTTPS**: Use TLS certificates for production
4. **Secrets**: Use environment variables or secret management

### Scalability

1. **Multiple Janus Instances**: Load balance across multiple Janus containers
2. **Database**: Replace in-memory store with Redis/PostgreSQL
3. **Message Queue**: Add Redis/RabbitMQ for async operations
4. **CDN**: Use CDN for static assets

### Example Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  janus:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    
  janus-api:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/vas
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET}
    
  redis:
    image: redis:alpine
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=vas
      - POSTGRES_USER=vas_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
```

## 🛠️ Development

### Local Development

```bash
# Start only Janus for development
docker-compose up janus

# Run FastAPI in development mode
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

### Testing

```bash
# Test camera addition
curl -X POST "http://localhost:3000/cameras" \
  -H "Content-Type: application/json" \
  -d @examples/test_camera.json

# Test stream info
curl "http://localhost:3000/cameras/test_cam/stream"
```

### API Documentation

Visit `http://localhost:3000/docs` for interactive API documentation with Swagger UI.

## 🔍 Troubleshooting

### Common Issues

1. **Camera Connection Failed**
   ```bash
   # Test RTSP connectivity
   ffprobe -rtsp_transport tcp rtsp://user:pass@camera.ip/stream
   ```

2. **WebRTC Connection Issues**
   - Check firewall rules for UDP ports 20000-20010
   - Verify STUN server connectivity
   - Check browser developer console for ICE errors

3. **Service Health Issues**
   ```bash
   # Check Janus status
   curl http://localhost:8088/janus/info
   
   # Check API service
   curl http://localhost:3000/health
   ```

### Logs Analysis

```bash
# Filter for specific camera errors
docker-compose logs janus | grep "camera_id"

# Monitor WebRTC connections
docker-compose logs janus | grep "WebRTC\|ICE\|DTLS"
```

## 📈 Future Enhancements

- [ ] Multi-camera simultaneous streaming
- [ ] Recording and playback capabilities  
- [ ] Motion detection integration
- [ ] Advanced analytics and alerts
- [ ] Mobile app SDK
- [ ] Edge computing support

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
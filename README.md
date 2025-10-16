# Video Analytics System (VAS) with Janus Gateway

## Overview
This system provides real-time RTSP camera feed streaming through WebRTC using Janus Gateway, integrated with a full-stack Video Analytics System (VAS) built with FastAPI backend and React frontend.

## Architecture

### Current Setup (2-Camera Local Testing)
- **Janus Gateway**: RTSP to WebRTC conversion
- **VAS Backend**: FastAPI with PostgreSQL database
- **VAS Frontend**: React TypeScript application  
- **Nginx**: Reverse proxy and load balancing
- **Live DVR**: Continuous recording with 30-second segments and timeline scrubber

### Future Setup (ASRock Edge Units)
- **Distributed Processing**: Each ASRock unit handles exactly 6 cameras
- **Local Inference**: YOLO object detection on Intel Arc 140T GPU
- **Central Dashboard**: Aggregates API endpoints from multiple units
- **Linear Scalability**: Add new units without re-engineering

## Project Structure

```
vas/
├── docker-compose.yml                    # Main 2-camera setup
├── docker-compose.asrock-edge.yml        # ASRock edge unit setup
├── scripts/deployment/deploy-edge.sh      # Edge deployment script
├── scripts/testing/test-local-regression.sh # Regression testing
├── test-camera-viewer.html               # HTML test page
├── adapter.js, janus.js                  # WebRTC libraries
│
├── janus/                                # Janus Gateway
│   ├── config/
│   │   ├── janus.jcfg                      # Main Janus config
│   │   ├── janus.plugin.streaming.jcfg     # 2-camera streaming
│   │   ├── edge-janus.jcfg                 # ASRock optimized config  
│   │   └── janus.plugin.streaming.edge.jcfg # 6-camera edge streaming
│   ├── api/                                # Custom Janus API service
│   └── Dockerfile                          # Janus container
│
├── backend/                             # FastAPI application
│   ├── app/                               # Core application
│   ├── add_sample_devices.py              # Database population
│   └── Dockerfile                         # Backend container
│
├── frontend/                           # React application
│   ├── src/                               # Source code
│   │   ├── components/VideoPlayer.tsx     # WebRTC video component with Live DVR
│   │   ├── components/TimelineScrubber.tsx # Timeline scrubber for recorded playback
│   │   └── pages/Streams.tsx              # Camera streams page
│   └── Dockerfile                         # Frontend container
│
├── edge-api/                            # ASRock Edge API
│   ├── main.py                            # FastAPI edge service
│   └── Dockerfile                         # Edge API container
│
├── config/nginx/nginx-dev.conf          # Main nginx config
└── config/nginx/nginx-edge.conf         # ASRock nginx config
```

## Quick Start

### First Time Setup (New Server Deployment)
```bash
# 1. Clone the repository
git clone <repository-url>
cd vas

# 2. Configure environment variables (OPTIONAL for development)
# Frontend configuration - only needed if accessing dev server from remote machine
cp frontend/.env.example frontend/.env
nano frontend/.env  # Update YOUR_SERVER_IP with actual IP (e.g., 10.30.250.245)

# Backend configuration (if needed)
cp backend/env.example backend/.env
nano backend/.env  # Update database and other settings

# Note: For production (port 80), no .env configuration is needed!
# The app auto-detects the server IP from the browser's location.

# 3. Start all services
docker-compose up --build -d

# 4. Add sample cameras to database
cd backend && python3 add_sample_devices.py

# 5. Access the system
# Production:        http://YOUR_SERVER_IP (port 80)
# Development:       http://YOUR_SERVER_IP:3002 (hot reload)
# Backend API:       http://YOUR_SERVER_IP:8000/docs
# Janus API:         http://YOUR_SERVER_IP:3000
```

### Local 2-Camera Setup (Already Configured)
```bash
# Start all services
docker-compose up --build -d

# Access the system
# Production:        http://localhost (port 80)
# Development:       http://localhost:3002 (hot reload)
# Backend API:       http://localhost:8000/docs
# Janus API:         http://localhost:3000
```

### Development Workflow
```bash
# For frontend development with hot reload (no Docker rebuilds)
cd frontend
npm start
# Access at: http://localhost:3002

# For production deployment
cd frontend
npm run build
docker-compose build vas-frontend
docker-compose up -d vas-frontend
# Access at: http://localhost (port 80)
```

### ASRock Edge Unit Deployment
```bash
# Deploy to ASRock unit
./scripts/deployment/deploy-edge.sh

# Test regression
./scripts/testing/test-local-regression.sh
```

## Camera Configuration

### Current Cameras (Local Testing)
- **Camera 1**: `rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp`
- **Camera 2**: `rtsp://root:G3M13m0b@172.16.16.123/live1s1.sdp`

### ASRock Edge Setup
- **6 Cameras per unit**: `172.16.16.122` - `172.16.16.127`
- **YOLO Processing**: Real-time 1080p/30fps object detection
- **GPU Acceleration**: Intel Arc 140T with 8 Xe cores

## Key Components

### WebRTC Streaming
- Direct RTSP to WebRTC conversion (no FFmpeg transcoding)
- H.264 passthrough for optimal performance
- ICE/STUN negotiation for NAT traversal

### Live DVR
- Continuous recording of camera streams
- 30-second segment recording using FFmpeg
- Timeline scrubber UI for browsing recorded footage
- Playback of historical segments
- Configurable retention period

### Database Schema
- Device management with UUIDs
- Stream configuration and status
- Recording segments and metadata
- Authentication and user management

### Edge Computing
- Distributed processing across ASRock units
- Local inference with Intel NPU/GPU acceleration
- Central aggregation for large-scale monitoring

## Testing

### Regression Testing
```bash
./scripts/testing/test-local-regression.sh
```

### Manual Testing
1. **Production**: `http://localhost` (port 80)
2. **Development**: `http://localhost:3002` (hot reload)
3. **API Testing**: `http://localhost:8000/docs`
4. **Janus API**: `http://localhost:3000`

## Performance Targets

### Local Setup (Current)
- 2 cameras at 1080p/30fps
- <100ms latency WebRTC streaming
- Stable concurrent viewing
- 30-second DVR segments

### ASRock Edge Setup (Future)
- 6 cameras at 1080p/30fps
- Real-time YOLO object detection
- <50ms inference latency
- Linear scalability to 300-500 cameras

## Port Configuration

### Production Ports
- **80**: Nginx reverse proxy (main access point)
- **5432**: PostgreSQL database
- **6379**: Redis cache
- **8000**: VAS Backend API
- **3000**: Janus API service

### Development Ports
- **3002**: React development server (hot reload)

### Janus Ports (network_mode: host)
- **8188**: Janus WebSocket
- **7088**: Janus Admin API
- **20000-20100**: RTP media ports

## API Endpoints

### VAS Backend
- `GET /api/devices` - List all cameras
- `GET /api/streams` - Stream management
- `POST /api/auth/login` - Authentication
- `GET /api/recordings/{device_id}/timeline` - Get DVR timeline
- `GET /api/recordings/{device_id}/segment/{segment_id}/play` - Play segment
- `POST /api/recordings/{device_id}/start` - Start Live DVR
- `POST /api/recordings/{device_id}/stop` - Stop Live DVR

### Janus API
- `GET /health` - Service health status
- `GET /streams` - Available video streams
- `POST /api/streams/configure` - Stream configuration

### Edge API
- `GET /health` - Unit health status
- `GET /metrics` - Performance metrics
- `POST /api/streams/configure` - Stream configuration

## Troubleshooting

### Common Issues
1. **No video feed**: Check Janus container status and camera URLs
2. **WebSocket errors**: Verify network_mode: host for Janus
3. **Database errors**: Run add_sample_devices.py to populate
4. **Container conflicts**: `docker-compose down --remove-orphans`
5. **Port conflicts**: Ensure port 80, 3000, and 8000 are available

### Debug Commands
```bash
# View logs
docker-compose logs -f janus-gateway
docker-compose logs -f vas-backend
docker-compose logs -f vas-frontend

# Check containers
docker-compose ps

# Restart services
docker-compose restart janus-gateway
docker-compose restart vas-backend

# Check ports
netstat -tlnp | grep -E ":80|:3002|:8000|:3000"

# View Live DVR recordings
ls -lh /home/atgin-rnd-ubuntu/vas/recordings/

# Check database segments
docker exec vas_backend python3 -c "from app.database import get_db; from app.models import RecordingSegment; print(list(next(get_db()).query(RecordingSegment).all()))"
```

## Roadmap

- [x] Basic RTSP to WebRTC streaming
- [x] React frontend integration
- [x] PostgreSQL database integration
- [x] Live DVR recording and playback
- [x] Timeline scrubber UI
- [x] ASRock edge unit architecture
- [ ] YOLO object detection integration
- [ ] Intel GPU acceleration
- [ ] Central dashboard aggregation
- [ ] Auto-scaling and load balancing

---

**Status**: Fully Functional - Local 2-camera setup with Live DVR working
**Next**: Deploy and test on ASRock hardware with 6-camera configuration

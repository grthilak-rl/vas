# Video Analytics System (VAS) with Janus Gateway

## 🎯 **Overview**
This system provides real-time RTSP camera feed streaming through WebRTC using Janus Gateway, integrated with a full-stack Video Analytics System (VAS) built with FastAPI backend and React frontend.

## 🏗️ **Architecture**

### **Current Setup (2-Camera Local Testing)**
- **Janus Gateway**: RTSP to WebRTC conversion
- **VAS Backend**: FastAPI with PostgreSQL database
- **VAS Frontend**: React TypeScript application  
- **Nginx**: Reverse proxy and load balancing

### **Future Setup (ASRock Edge Units)**
- **Distributed Processing**: Each ASRock unit handles exactly 6 cameras
- **Local Inference**: YOLO object detection on Intel Arc 140T GPU
- **Central Dashboard**: Aggregates API endpoints from multiple units
- **Linear Scalability**: Add new units without re-engineering

## 📁 **Project Structure**

```
vas-test/
├── 🐳 docker-compose.yml                    # Main 2-camera setup
├── 🐳 docker-compose.asrock-edge.yml        # ASRock edge unit setup
├── 🚀 scripts/deployment/deploy-edge.sh      # Edge deployment script
├── 🧪 scripts/testing/test-local-regression.sh # Regression testing
├── 📄 test-camera-viewer.html               # HTML test page
├── 📄 adapter.js, janus.js                  # WebRTC libraries
│
├── 🎮 janus/                                # Janus Gateway
│   ├── config/
│   │   ├── janus.jcfg                      # Main Janus config
│   │   ├── janus.plugin.streaming.jcfg     # 2-camera streaming
│   │   ├── edge-janus.jcfg                 # ASRock optimized config  
│   │   └── janus.plugin.streaming.edge.jcfg # 6-camera edge streaming
│   ├── api/                                # Custom Janus API service
│   └── Dockerfile                          # Janus container
│
├── 🏭 vas/                                  # Video Analytics System
│   ├── backend/                            # FastAPI application
│   │   ├── app/                           # Core application
│   │   ├── add_sample_devices.py          # Database population
│   │   └── Dockerfile                     # Backend container
│   └── frontend/                          # React application
│       ├── src/                           # Source code
│       │   ├── components/SimpleVideoPlayer.tsx  # WebRTC video component
│       │   └── pages/Streams.tsx          # Camera streams page
│       └── Dockerfile                     # Frontend container
│
├── 🌐 edge-api/                            # ASRock Edge API
│   ├── main.py                            # FastAPI edge service
│   └── Dockerfile                         # Edge API container
│
├── ⚙️ config/nginx/nginx-dev.conf          # Main nginx config
└── ⚙️ config/nginx/nginx-edge.conf         # ASRock nginx config
```

## 🚀 **Quick Start**

### **Local 2-Camera Setup**
```bash
# Start all services
docker-compose up --build -d

# Add sample cameras to database
cd vas/backend && python3 add_sample_devices.py

# Access the system
# Frontend:     http://localhost:3001
# Backend API:  http://localhost:8000/docs
# Test Page:    http://localhost:8082/test-camera-viewer.html
```

### **ASRock Edge Unit Deployment**
```bash
# Deploy to ASRock unit
./scripts/deployment/deploy-edge.sh

# Test regression
./scripts/testing/test-local-regression.sh
```

## 📹 **Camera Configuration**

### **Current Cameras (Local Testing)**
- **Camera 1**: `rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp`
- **Camera 2**: `rtsp://root:G3M13m0b@172.16.16.123/live1s1.sdp`

### **ASRock Edge Setup**
- **6 Cameras per unit**: `172.16.16.122` - `172.16.16.127`
- **YOLO Processing**: Real-time 1080p/30fps object detection
- **GPU Acceleration**: Intel Arc 140T with 8 Xe cores

## 🔧 **Key Components**

### **WebRTC Streaming**
- Direct RTSP to WebRTC conversion (no FFmpeg transcoding)
- H.264 passthrough for optimal performance
- ICE/STUN negotiation for NAT traversal

### **Database Schema**
- Device management with UUIDs
- Stream configuration and status
- Authentication and user management

### **Edge Computing**
- Distributed processing across ASRock units
- Local inference with Intel NPU/GPU acceleration
- Central aggregation for large-scale monitoring

## 🧪 **Testing**

### **Regression Testing**
```bash
./scripts/testing/test-local-regression.sh
```

### **Manual Testing**
1. **HTML Test**: `http://localhost:8082/test-camera-viewer.html`
2. **React Frontend**: `http://localhost:3001` → Streams page
3. **API Testing**: `http://localhost:8000/docs`

## 📊 **Performance Targets**

### **Local Setup (Current)**
- ✅ 2 cameras at 1080p/30fps
- ✅ <100ms latency WebRTC streaming
- ✅ Stable concurrent viewing

### **ASRock Edge Setup (Future)**
- 🎯 6 cameras at 1080p/30fps
- 🎯 Real-time YOLO object detection
- 🎯 <50ms inference latency
- 🎯 Linear scalability to 300-500 cameras

## 🔗 **API Endpoints**

### **VAS Backend**
- `GET /api/devices` - List all cameras
- `GET /api/streams` - Stream management
- `POST /auth/login` - Authentication

### **Edge API**
- `GET /health` - Unit health status
- `GET /metrics` - Performance metrics
- `POST /api/streams/configure` - Stream configuration

## 🛠️ **Troubleshooting**

### **Common Issues**
1. **No video feed**: Check Janus container status and camera URLs
2. **WebSocket errors**: Verify network_mode: host for Janus
3. **Database errors**: Run add_sample_devices.py to populate
4. **Container conflicts**: `docker-compose down --remove-orphans`

### **Debug Commands**
```bash
# View logs
docker-compose logs -f janus-gateway
docker-compose logs -f vas-backend

# Check containers
docker-compose ps

# Restart services
docker-compose restart janus-gateway
```

## 📈 **Roadmap**

- [x] Basic RTSP to WebRTC streaming
- [x] React frontend integration
- [x] PostgreSQL database integration
- [x] ASRock edge unit architecture
- [ ] YOLO object detection integration
- [ ] Intel GPU acceleration
- [ ] Central dashboard aggregation
- [ ] Auto-scaling and load balancing

---

**Status**: ✅ **Fully Functional** - Local 2-camera setup working perfectly
**Next**: Deploy and test on ASRock hardware with 6-camera configuration

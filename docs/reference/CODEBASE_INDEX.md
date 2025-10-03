# VAS Codebase Index

## 🎯 **System Overview**

The Video Analytics System (VAS) is a distributed edge computing platform for real-time camera feed processing and streaming. It supports both local development (2-camera setup) and production edge deployment (6-camera ASRock units) with linear scalability.

## 📁 **Directory Structure**

```
vas/
├── 🐳 docker-compose.yml                    # Main 2-camera setup
├── 🐳 docker-compose.asrock-edge.yml        # ASRock edge unit setup
├── 🚀 scripts/deployment/deploy-edge.sh      # Edge deployment script
├── 🧪 test-local-regression.sh              # Regression testing
├── 📄 test-camera-viewer.html               # HTML test page
├── 📄 adapter.js, janus.js                  # WebRTC libraries
│
├── 🎮 janus/                                # Janus Gateway
│   ├── config/                              # Janus configuration files
│   ├── api/                                 # Custom Janus API service
│   ├── examples/                            # Integration examples
│   ├── html/                                # Test HTML pages
│   └── Dockerfile                           # Janus container
│
├── 🏭 vas/                                  # Video Analytics System
│   ├── backend/                             # FastAPI application
│   ├── frontend/                            # React application
│   ├── nginx/                               # Nginx configuration
│   └── scripts/                             # Utility scripts
│
├── 🌐 edge-api/                             # ASRock Edge API
├── ⚙️ nginx.conf, nginx-edge.conf           # Nginx configurations
├── 📚 docs/                                 # Documentation files
└── 🔧 scripts/                              # Deployment and utility scripts
```

## 🏗️ **Core Components**

### 1. **Janus WebRTC Gateway**
- **Purpose**: Real-time video streaming from RTSP cameras to web browsers
- **Location**: `janus/`
- **Key Features**:
  - Direct RTSP to WebRTC conversion
  - H.264 passthrough (no transcoding)
  - Low-latency streaming (< 100ms)
  - WebSocket and HTTP API support
  - ICE/STUN for NAT traversal

**Configuration Files**:
- `janus/config/janus.jcfg` - Main Janus configuration
- `janus/config/edge-janus.jcfg` - ASRock optimized configuration
- `janus/config/janus.plugin.streaming.jcfg` - 2-camera streaming config
- `janus/config/janus.plugin.streaming.edge.jcfg` - 6-camera edge config
- `janus/config/janus.transport.websockets.jcfg` - WebSocket transport

**Key Endpoints**:
- HTTP API: Port 8088
- WebSocket: Port 8188
- Admin API: Port 7088

### 2. **VAS Backend (FastAPI)**
- **Purpose**: Device management, authentication, and API orchestration
- **Location**: `backend/`
- **Technology Stack**:
  - Python 3.11 with FastAPI
  - SQLAlchemy ORM with PostgreSQL
  - Pydantic for data validation
  - Uvicorn ASGI server

**Key API Endpoints**:
- `POST /api/auth/login-json` - Authentication
- `GET /api/devices/` - List all devices
- `POST /api/devices/` - Create new device
- `GET /api/devices/{id}` - Get device details
- `POST /api/devices/validate` - Validate RTSP stream
- `POST /api/discover/` - Start device discovery
- `GET /api/streams/` - List available streams

**Database Schema**:
- Devices table with UUID primary keys
- Stream configuration and status
- Authentication and user management

### 3. **VAS Frontend (React)**
- **Purpose**: Web-based user interface for camera monitoring
- **Location**: `frontend/`
- **Technology Stack**:
  - React 18 with TypeScript
  - Material-UI (MUI) components
  - React Router for navigation
  - React Query for data fetching
  - WebRTC for video streaming

**Key Components**:
- `src/components/VideoPlayer.tsx` - WebRTC video player
- `src/pages/Streams.tsx` - Camera streams page
- `src/pages/Devices.tsx` - Device management
- `src/pages/Dashboard.tsx` - System overview
- `src/contexts/AuthContext.tsx` - Authentication context

### 4. **Edge API Service**
- **Purpose**: Local edge unit management and central reporting
- **Location**: `edge-api/`
- **Key Features**:
  - Unit-specific configuration management
  - Health and metrics reporting
  - Camera stream configuration
  - Central dashboard integration

**Endpoints**:
- `GET /health` - Unit health status
- `GET /metrics` - Performance metrics
- `POST /api/streams/configure` - Stream setup

### 5. **AI Integration (External)**
- **Purpose**: AI applications can consume VAS video feeds
- **Integration**: Via VAS APIs and WebRTC streams
- **Note**: AI inference should be implemented as separate applications
  - VAS provides video processing and streaming
  - AI applications consume video feeds via APIs
  - Separation of concerns for better maintainability
  - 1080p/30fps processing capability
  - Object tracking and analytics

## 🔧 **Configuration Management**

### **Critical Configuration Files**

1. **Docker Compose**:
   - `docker-compose.yml` - Local 2-camera setup
   - `docker-compose.asrock-edge.yml` - ASRock edge deployment

2. **Janus Configuration**:
   - `janus/config/janus.jcfg` - Main gateway config
   - `janus/config/edge-janus.jcfg` - Edge optimized config
   - `janus/config/janus.plugin.streaming.jcfg` - Streaming plugin
   - `janus/config/janus.plugin.streaming.edge.jcfg` - Edge streaming

3. **Nginx Configuration**:
   - `nginx.conf` - Main nginx config
   - `nginx-edge.conf` - Edge nginx config

4. **Environment Variables**:
   - `backend/env.example` - Backend environment template
   - Unit-specific variables in deployment scripts

### **Camera Configuration**
- **Local Setup**: 2 cameras (172.16.16.122, 172.16.16.123)
- **Edge Setup**: 6 cameras (172.16.16.122-127)
- **RTSP Authentication**: Digest method with specific credentials
- **Video Codec**: H.264 passthrough for optimal performance

## 🚀 **Deployment & Automation**

### **Deployment Scripts**

1. **`scripts/deployment/deploy-edge.sh`** - ASRock Edge Deployment
   - Automated deployment for ASRock iEP-7040E-024 units
   - Hardware-optimized configuration
   - Unit management with unique IDs
   - Health monitoring and validation

2. **`test-local-regression.sh`** - Regression Testing
   - Tests existing 2-camera setup
   - Validates configuration syntax
   - Performance benchmarking
   - Configuration comparison

3. **`backup-config.sh`** - Configuration Backup
   - Complete system backup
   - Docker state information
   - System information capture
   - Recovery instructions

4. **`recover.sh`** - System Recovery
   - Quick recovery from backups
   - Emergency backup before recovery
   - Dry-run mode for preview
   - Automatic verification

### **Deployment Workflows**

**Local Development**:
```bash
docker-compose up --build -d
```

**Regression Testing**:
```bash
./test-local-regression.sh
```

**Edge Deployment**:
```bash
./scripts/deployment/deploy-edge.sh --unit-id 001
```

## 📊 **Performance Characteristics**

### **Local Setup (2 cameras)**
- Target: 1080p/30fps per camera
- Latency: < 100ms end-to-end
- Concurrent viewers: 10+ per stream
- Hardware: Standard development machine

### **Edge Setup (6 cameras)**
- Target: 1080p/30fps per camera
- AI Inference: Real-time YOLO processing
- Hardware: Intel Core Ultra 7 255H + Intel Arc 140T
- Memory: 16GB system requirement
- Storage: NVMe for model caching

### **Large Scale (300-500 cameras)**
- Deployment: 50-85 ASRock units
- Architecture: Distributed edge processing
- Central: API aggregation only
- Bandwidth: Minimal central requirements

## 🔍 **Key Integration Points**

### **WebRTC Streaming Flow**
1. **RTSP Ingestion**: Cameras stream H.264 via RTSP
2. **Janus Conversion**: Direct RTSP to WebRTC conversion
3. **Browser Delivery**: WebRTC streams via WebSocket
4. **Real-time Display**: HTML5 video elements

### **API Integration**
- **Backend API**: FastAPI with OpenAPI documentation
- **Janus API**: HTTP (8088) and WebSocket (8188) endpoints
- **Edge API**: Unit-specific management and reporting
- **Frontend API**: React Query for efficient data fetching

### **Database Integration**
- **PostgreSQL**: Primary database for device management
- **Redis**: Caching and session management
- **Alembic**: Database migrations
- **SQLAlchemy**: ORM for database operations

## 🛠️ **Development Tools**

### **Testing**
- **Regression Tests**: `test-local-regression.sh`
- **API Tests**: `backend/test_api.py`
- **HTML Test Page**: `test-camera-viewer.html`
- **WebRTC Test**: `webrtc-api-test.html`

### **Monitoring**
- **Health Checks**: Docker container health checks
- **Performance Metrics**: CPU/GPU utilization monitoring
- **Log Aggregation**: Structured JSON logging
- **Error Tracking**: Application-level error handling

### **Documentation**
- **API Documentation**: OpenAPI/Swagger at `/docs`
- **Architecture Docs**: `ARCHITECTURE.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **WebRTC Reference**: `VAS_WebRTC_Quick_Reference.md`

## 🔐 **Security & Authentication**

### **Authentication System**
- **JWT-based**: Token-based authentication
- **Default Credentials**: admin/admin123
- **Role-based Access**: Planned for future
- **Session Management**: Redis-based sessions

### **Network Security**
- **Container Isolation**: Docker network isolation
- **HTTPS Termination**: Nginx SSL termination
- **RTSP Security**: Digest authentication
- **API Security**: CORS and authentication middleware

## 📈 **Scalability Design**

### **Horizontal Scaling**
- **Edge Units**: Independent ASRock units
- **Linear Scaling**: Add units without re-engineering
- **Unit IDs**: Unique identification (001, 002, 050)
- **Central Aggregation**: API endpoint aggregation

### **Resource Management**
- **CPU Allocation**: Optimized for Intel Core Ultra 7 255H
- **GPU Acceleration**: Intel Arc 140T for AI inference
- **Memory Management**: 16GB system requirement
- **Storage Optimization**: NVMe for model caching

## 🚨 **Troubleshooting**

### **Common Issues**
1. **No Video Feed**: Check Janus container status and camera URLs
2. **WebSocket Errors**: Verify network_mode: host for Janus
3. **Database Errors**: Run add_sample_devices.py to populate
4. **Container Conflicts**: `docker-compose down --remove-orphans`

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

### **Health Checks**
```bash
# Janus API
curl -s http://localhost:8088/janus/info

# Backend API
curl -s http://localhost:8000/api/health

# RTSP Stream
curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp
```

## 🎯 **Future Roadmap**

### **Completed Features**
- [x] Basic RTSP to WebRTC streaming
- [x] React frontend integration
- [x] PostgreSQL database integration
- [x] ASRock edge unit architecture
- [x] Deployment automation
- [x] Regression testing

### **Planned Features**
- [ ] YOLO object detection integration
- [ ] Intel GPU acceleration
- [ ] Central dashboard aggregation
- [ ] Auto-scaling and load balancing
- [ ] Advanced analytics and AI
- [ ] Mobile applications

## 📚 **Additional Resources**

### **Documentation Files**
- `VAS_FLOW_DIAGRAM.md` - System flow visualization
- `VAS_WebRTC_Quick_Reference.md` - WebRTC implementation guide
- `VAS_SYSTEM_FLOW_DOCUMENTATION.md` - Detailed flow documentation
- `VAS_TROUBLESHOOTING_QUICK_REFERENCE.md` - Troubleshooting guide
- `WebRTC_API_Gateway_Documentation.md` - API gateway documentation
- `GPU_SCALING_GUIDE.md` - GPU scaling guide
- `CROSS_SERVER_DEPLOYMENT_GUIDE.md` - Cross-server deployment

### **Test Files**
- `test-camera-viewer.html` - HTML test page
- `webrtc-api-test.html` - WebRTC API test
- `webrtc-api-simple-test.html` - Simple WebRTC test
- `test_multiple_connections.py` - Multiple connection test
- `serve_test_page.py` - Test page server

### **Backup & Recovery**
- `backups/` - Configuration backups
- `backup-config.sh` - Backup script
- `recover.sh` - Recovery script
- `recover.sh` - Recovery script

---

**Status**: ✅ **Fully Functional** - Local 2-camera setup working perfectly
**Next**: Deploy and test on ASRock hardware with 6-camera configuration

This index provides a comprehensive overview of the VAS codebase structure, components, and functionality for future development and maintenance.

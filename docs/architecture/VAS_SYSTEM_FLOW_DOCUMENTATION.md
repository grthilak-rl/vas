# VAS System Flow Documentation

## 🎯 **Purpose**
This document explains the complete flow of the VAS system, including when each configuration file is accessed, so you can trace exactly where failures occur.

## 🏗️ **System Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VAS Frontend  │    │  VAS Backend    │    │  Janus Gateway  │
│   (React App)   │◄──►│   (FastAPI)     │◄──►│   (WebRTC)      │
│   Port: 80       │    │   Port: 8000    │    │   Port: 8088    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   PostgreSQL    │    │   RTSP Cameras  │
│   Port: 80       │    │   Port: 5432   │    │   Port: 554     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │   Redis Cache   │    │   Stream Data   │
│   frontend-dist │    │   Port: 6379    │    │   H.264 Video   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **System Startup Flow**

### **1. Docker Compose Initialization**
**File**: `docker-compose.asrock-edge.yml`
**Access Point**: System startup
**Purpose**: Defines all services and their relationships

```yaml
services:
  edge-db:          # PostgreSQL database
  edge-redis:       # Redis cache
  janus-edge:       # Janus WebRTC Gateway
  vas-backend-edge: # FastAPI backend
  nginx-edge:       # Nginx reverse proxy
```

**Configuration Files Accessed**:
- `docker-compose.asrock-edge.yml` - Service definitions
- `janus/Dockerfile` - Custom Janus build
- Environment variables for each service

### **2. Database Initialization**
**Service**: `edge-db`
**Access Point**: Container startup
**Purpose**: Initialize PostgreSQL database

**Configuration Files Accessed**:
- Database environment variables in `docker-compose.asrock-edge.yml`
- Database schema files (if any)

**Flow**:
```
Container Start → PostgreSQL Init → Database Ready → Port 5432 Open
```

### **3. Redis Initialization**
**Service**: `edge-redis`
**Access Point**: Container startup
**Purpose**: Initialize Redis cache

**Configuration Files Accessed**:
- Redis environment variables in `docker-compose.asrock-edge.yml`

**Flow**:
```
Container Start → Redis Init → Cache Ready → Port 6379 Open
```

### **4. Janus Gateway Initialization**
**Service**: `janus-edge`
**Access Point**: Container startup
**Purpose**: Initialize WebRTC Gateway

**Configuration Files Accessed** (in order):
1. `janus/Dockerfile` - Custom build process
2. `janus/config/janus.jcfg` - Main Janus configuration
3. `janus/config/janus.transport.http.jcfg` - HTTP transport
4. `janus/config/janus.transport.websockets.jcfg` - WebSocket transport
5. `janus/config/janus.plugin.streaming.jcfg` - Streaming plugin
6. `janus/config/janus.plugin.streaming.edge.jcfg` - Edge-specific streams

**Flow**:
```
Container Start → Custom Build → Config Load → Plugin Init → RTSP Connect → Ready
```

**Critical Configuration Files**:
- `janus.jcfg` - Main gateway settings
- `janus.transport.websockets.jcfg` - WebSocket settings (Port 8188)
- `janus.transport.http.jcfg` - HTTP API settings (Port 8088)
- `janus.plugin.streaming.jcfg` - Streaming plugin settings
- `janus.plugin.streaming.edge.jcfg` - RTSP stream definitions

### **5. VAS Backend Initialization**
**Service**: `vas-backend-edge`
**Access Point**: Container startup
**Purpose**: Initialize FastAPI backend

**Configuration Files Accessed**:
- Environment variables in `docker-compose.asrock-edge.yml`
- `vas/backend/app/core/constants.py` - Device mappings
- `vas/backend/app/schemas.py` - API schemas

**Flow**:
```
Container Start → Database Connect → Redis Connect → Janus Connect → API Ready
```

**Critical Configuration Files**:
- `vas/backend/app/core/constants.py` - `DEVICE_TO_MOUNTPOINT_MAP`
- `vas/backend/app/schemas.py` - API data models

### **6. Nginx Initialization**
**Service**: `nginx-edge`
**Access Point**: Container startup
**Purpose**: Initialize reverse proxy

**Configuration Files Accessed**:
- `nginx-edge.conf` - Nginx configuration

**Flow**:
```
Container Start → Config Load → Proxy Setup → Port 80 Open
```

**Critical Configuration Files**:
- `nginx-edge.conf` - Proxy rules and static file serving

## 🔄 **Runtime Flow**

### **1. User Access Flow**
**Entry Point**: Browser → `http://localhost`

**Flow**:
```
Browser Request → Nginx (Port 80) → Static Files (frontend-dist) → React App Load
```

**Configuration Files Accessed**:
- `nginx-edge.conf` - Static file serving rules

### **2. Frontend Initialization**
**Component**: React App
**Access Point**: Browser load

**Configuration Files Accessed**:
- `frontend/public/index.html` - Janus library loading
- `frontend/src/App.tsx` - Main app structure
- `frontend/src/components/VideoPlayer.tsx` - WebRTC implementation

**Flow**:
```
React App Load → Janus Libraries Load → Component Mount → State Init
```

### **3. Authentication Flow**
**Entry Point**: Frontend → Backend API

**Flow**:
```
Frontend → POST /api/auth/login → Backend → Database Check → JWT Token → Frontend
```

**Configuration Files Accessed**:
- `vas/backend/app/api/auth.py` - Authentication endpoints
- `vas/backend/app/core/security.py` - JWT handling

### **4. Device List Flow**
**Entry Point**: Frontend → Backend API

**Flow**:
```
Frontend → GET /api/devices → Backend → Database Query → Device List → Frontend
```

**Configuration Files Accessed**:
- `vas/backend/app/api/devices.py` - Device endpoints
- `vas/backend/app/core/constants.py` - Device mappings

### **5. Video Stream Flow**
**Entry Point**: Frontend → Janus Gateway

**Flow**:
```
Frontend → Janus WebSocket (Port 8188) → Streaming Plugin → RTSP Stream → WebRTC → Frontend
```

**Configuration Files Accessed**:
- `janus/config/janus.transport.websockets.jcfg` - WebSocket settings
- `janus/config/janus.plugin.streaming.jcfg` - Plugin settings
- `janus/config/janus.plugin.streaming.edge.jcfg` - Stream definitions

## 🔍 **Configuration File Access Points**

### **Janus Configuration Files**

#### **`janus.jcfg`**
- **Accessed**: Janus container startup
- **Purpose**: Main gateway configuration
- **Critical Settings**: Logging, plugins, transports
- **Failure Point**: Janus won't start

#### **`janus.transport.http.jcfg`**
- **Accessed**: Janus container startup
- **Purpose**: HTTP API configuration
- **Critical Settings**: Port 8088, CORS, admin access
- **Failure Point**: HTTP API unavailable

#### **`janus.transport.websockets.jcfg`**
- **Accessed**: Janus container startup
- **Purpose**: WebSocket transport configuration
- **Critical Settings**: Port 8188, secure WebSocket
- **Failure Point**: WebRTC connections fail

#### **`janus.plugin.streaming.jcfg`**
- **Accessed**: Janus container startup
- **Purpose**: Streaming plugin configuration
- **Critical Settings**: Plugin enabled, debug level
- **Failure Point**: Streaming plugin not loaded

#### **`janus.plugin.streaming.edge.jcfg`**
- **Accessed**: Janus container startup
- **Purpose**: RTSP stream definitions
- **Critical Settings**: Stream URLs, authentication, codecs
- **Failure Point**: No video streams available

### **Backend Configuration Files**

#### **`vas/backend/app/core/constants.py`**
- **Accessed**: Backend startup, device operations
- **Purpose**: Device-to-mountpoint mappings
- **Critical Settings**: `DEVICE_TO_MOUNTPOINT_MAP`
- **Failure Point**: "No proxy mountpoint configured"

#### **`vas/backend/app/schemas.py`**
- **Accessed**: API requests
- **Purpose**: Data validation schemas
- **Critical Settings**: Device schemas, update schemas
- **Failure Point**: API validation errors

### **Frontend Configuration Files**

#### **`frontend/public/index.html`**
- **Accessed**: Browser load
- **Purpose**: Janus library loading
- **Critical Settings**: Janus script tags
- **Failure Point**: WebRTC functionality unavailable

#### **`frontend/src/components/VideoPlayer.tsx`**
- **Accessed**: Component mount
- **Purpose**: WebRTC implementation
- **Critical Settings**: Janus connection, SDP handling
- **Failure Point**: Video streams don't display

### **Infrastructure Configuration Files**

#### **`docker-compose.asrock-edge.yml`**
- **Accessed**: System startup
- **Purpose**: Service definitions and networking
- **Critical Settings**: Ports, volumes, environment variables
- **Failure Point**: Services won't start

#### **`nginx-edge.conf`**
- **Accessed**: Nginx startup
- **Purpose**: Reverse proxy configuration
- **Critical Settings**: Proxy rules, static file serving
- **Failure Point**: Frontend inaccessible

## 🚨 **Failure Tracing Guide**

### **1. System Won't Start**
**Check Order**:
1. `docker-compose.asrock-edge.yml` - Service definitions
2. `janus/Dockerfile` - Custom build process
3. Environment variables - Database URLs, ports

**Common Issues**:
- Wrong database IP addresses
- Port conflicts
- Missing environment variables

### **2. Janus Won't Start**
**Check Order**:
1. `janus.jcfg` - Main configuration
2. `janus.transport.http.jcfg` - HTTP transport
3. `janus.transport.websockets.jcfg` - WebSocket transport
4. `janus.plugin.streaming.jcfg` - Plugin configuration

**Common Issues**:
- Invalid configuration syntax
- Port conflicts
- Plugin not enabled

### **3. No Video Streams**
**Check Order**:
1. `janus.plugin.streaming.edge.jcfg` - Stream definitions
2. RTSP URLs and authentication
3. Network connectivity to cameras
4. `vas/backend/app/core/constants.py` - Device mappings

**Common Issues**:
- Wrong RTSP URLs
- Authentication failures
- Device ID mismatches
- Network connectivity

### **4. Frontend Can't Connect**
**Check Order**:
1. `nginx-edge.conf` - Proxy configuration
2. `frontend/public/index.html` - Janus libraries
3. `frontend/src/components/VideoPlayer.tsx` - WebRTC code
4. Backend API availability

**Common Issues**:
- Janus libraries not loaded
- WebSocket connection failures
- API authentication issues

### **5. Backend API Errors**
**Check Order**:
1. Database connectivity
2. Redis connectivity
3. `vas/backend/app/core/constants.py` - Device mappings
4. `vas/backend/app/schemas.py` - Data validation

**Common Issues**:
- Database connection failures
- Device ID mismatches
- Schema validation errors

## 🔧 **Debugging Commands**

### **Check Service Status**
```bash
# Check all services
docker-compose -f docker-compose.asrock-edge.yml ps

# Check specific service logs
docker logs janus-edge-001
docker logs vas-backend-edge-001
docker logs nginx-edge-001
```

### **Check Configuration Loading**
```bash
# Check Janus configuration
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.jcfg

# Check streaming plugin configuration
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.plugin.streaming.jcfg
```

### **Check Network Connectivity**
```bash
# Check Janus API
curl -s http://localhost:8088/janus/info

# Check backend API
curl -s http://localhost:8000/api/health

# Check RTSP streams
curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp
```

### **Check Device Mappings**
```bash
# Check device list
curl -s http://localhost:8000/api/devices/ | jq

# Check specific device
curl -s http://localhost:8000/api/devices/05a9a734-f76d-4f45-9b0e-1e9c89b43e2c | jq
```

## 📋 **Configuration File Checklist**

### **Before Deployment**
- [ ] `docker-compose.asrock-edge.yml` - Correct IP addresses
- [ ] `janus.jcfg` - Valid syntax
- [ ] `janus.transport.websockets.jcfg` - Port 8188
- [ ] `janus.transport.http.jcfg` - Port 8088
- [ ] `janus.plugin.streaming.jcfg` - Plugin enabled
- [ ] `janus.plugin.streaming.edge.jcfg` - Valid RTSP URLs
- [ ] `vas/backend/app/core/constants.py` - Device mappings
- [ ] `nginx-edge.conf` - Proxy rules

### **After Deployment**
- [ ] All services running
- [ ] Janus API responding
- [ ] Backend API responding
- [ ] RTSP streams active
- [ ] Frontend accessible
- [ ] Video streams working

## 🎯 **Quick Failure Diagnosis**

### **"No video feed"**
1. Check Janus logs for `[stream-1]` and `[stream-2]`
2. Verify RTSP URLs in `janus.plugin.streaming.edge.jcfg`
3. Check device mappings in `vas/backend/app/core/constants.py`
4. Test RTSP connectivity directly

### **"Connection refused"**
1. Check service status with `docker ps`
2. Verify port configurations
3. Check network connectivity
4. Review service logs

### **"Authentication failed"**
1. Check RTSP credentials in `janus.plugin.streaming.edge.jcfg`
2. Verify device authentication in backend
3. Check JWT token handling

### **"No proxy mountpoint"**
1. Check `DEVICE_TO_MOUNTPOINT_MAP` in `vas/backend/app/core/constants.py`
2. Verify device IDs in database
3. Check Janus streaming plugin configuration

---

**This documentation provides a complete trace of the VAS system flow, enabling you to quickly identify where failures occur and which configuration files to check.**

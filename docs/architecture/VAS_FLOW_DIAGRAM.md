# VAS System Flow Diagram

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                VAS SYSTEM FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Nginx Proxy   │    │   VAS Backend   │    │   Janus Gateway │
│   (User)        │◄──►│   Port: 80      │◄──►│   Port: 8000    │◄──►│   Port: 8088    │
│                 │    │                 │    │                 │    │   Port: 8188    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Static Files  │    │   PostgreSQL   │    │   RTSP Streams  │
│   (Frontend)    │    │   frontend-dist │    │   Port: 5432   │    │   Port: 554     │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebRTC        │    │   Nginx Config  │    │   Redis Cache   │    │   H.264 Video   │
│   Video Player  │    │   nginx-edge.conf│    │   Port: 6379   │    │   Data Stream   │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 **Startup Flow Sequence**

```
1. Docker Compose Start
   ├── docker-compose.asrock-edge.yml
   └── Environment Variables

2. Database Initialization
   ├── edge-db (PostgreSQL)
   └── Port 5432 Open

3. Redis Initialization
   ├── edge-redis
   └── Port 6379 Open

4. Janus Gateway Initialization
   ├── janus/Dockerfile (Custom Build)
   ├── janus.jcfg (Main Config)
   ├── janus.transport.http.jcfg (HTTP API)
   ├── janus.transport.websockets.jcfg (WebSocket)
   ├── janus.plugin.streaming.jcfg (Plugin)
   ├── janus.plugin.streaming.edge.jcfg (Streams)
   └── RTSP Connection to Cameras

5. VAS Backend Initialization
   ├── Database Connection
   ├── Redis Connection
   ├── Janus Connection
   ├── vas/backend/app/core/constants.py (Device Mappings)
   └── API Ready (Port 8000)

6. Nginx Initialization
   ├── nginx-edge.conf (Proxy Config)
   └── Port 80 Open
```

## 🎯 **Runtime Flow Sequence**

```
1. User Access
   Browser → http://localhost → Nginx → Static Files → React App

2. Frontend Initialization
   React App → Janus Libraries → Component Mount → State Init

3. Authentication Flow
   Frontend → POST /api/auth/login → Backend → Database → JWT Token

4. Device List Flow
   Frontend → GET /api/devices → Backend → Database → Device List

5. Video Stream Flow
   Frontend → Janus WebSocket (8188) → Streaming Plugin → RTSP → WebRTC
```

## 🔍 **Configuration File Access Points**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION FILE ACCESS                            │
└─────────────────────────────────────────────────────────────────────────────────┘

STARTUP PHASE:
├── docker-compose.asrock-edge.yml
│   └── Accessed: System startup
│   └── Purpose: Service definitions, networking, environment variables
│
├── janus/Dockerfile
│   └── Accessed: Janus container build
│   └── Purpose: Custom Janus build with libcurl 7.87.0
│
├── janus.jcfg
│   └── Accessed: Janus container startup
│   └── Purpose: Main gateway configuration
│
├── janus.transport.http.jcfg
│   └── Accessed: Janus container startup
│   └── Purpose: HTTP API configuration (Port 8088)
│
├── janus.transport.websockets.jcfg
│   └── Accessed: Janus container startup
│   └── Purpose: WebSocket transport (Port 8188)
│
├── janus.plugin.streaming.jcfg
│   └── Accessed: Janus container startup
│   └── Purpose: Streaming plugin configuration
│
└── janus.plugin.streaming.edge.jcfg
    └── Accessed: Janus container startup
    └── Purpose: RTSP stream definitions

RUNTIME PHASE:
├── nginx-edge.conf
│   └── Accessed: Nginx startup
│   └── Purpose: Reverse proxy configuration
│
├── vas/backend/app/core/constants.py
│   └── Accessed: Backend startup, device operations
│   └── Purpose: Device-to-mountpoint mappings
│
├── vas/backend/app/schemas.py
│   └── Accessed: API requests
│   └── Purpose: Data validation schemas
│
├── frontend/public/index.html
│   └── Accessed: Browser load
│   └── Purpose: Janus library loading
│
└── frontend/src/components/VideoPlayer.tsx
    └── Accessed: Component mount
    └── Purpose: WebRTC implementation
```

## 🚨 **Failure Points & Diagnosis**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FAILURE DIAGNOSIS                                │
└─────────────────────────────────────────────────────────────────────────────────┘

SYSTEM WON'T START:
├── Check: docker-compose.asrock-edge.yml
├── Check: Environment variables
├── Check: Port conflicts
└── Command: docker-compose -f docker-compose.asrock-edge.yml ps

JANUS WON'T START:
├── Check: janus.jcfg (syntax)
├── Check: janus.transport.*.jcfg (ports)
├── Check: janus.plugin.streaming.jcfg (plugin enabled)
└── Command: docker logs janus-edge-001

NO VIDEO STREAMS:
├── Check: janus.plugin.streaming.edge.jcfg (RTSP URLs)
├── Check: RTSP authentication
├── Check: vas/backend/app/core/constants.py (device mappings)
└── Command: curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp

FRONTEND CAN'T CONNECT:
├── Check: nginx-edge.conf (proxy rules)
├── Check: frontend/public/index.html (Janus libraries)
├── Check: frontend/src/components/VideoPlayer.tsx (WebRTC code)
└── Command: curl -s http://localhost:8088/janus/info

BACKEND API ERRORS:
├── Check: Database connectivity
├── Check: Redis connectivity
├── Check: vas/backend/app/core/constants.py (device mappings)
└── Command: curl -s http://localhost:8000/api/health
```

## 🔧 **Quick Debug Commands**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DEBUG COMMANDS                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

SERVICE STATUS:
docker-compose -f docker-compose.asrock-edge.yml ps

SERVICE LOGS:
docker logs janus-edge-001
docker logs vas-backend-edge-001
docker logs nginx-edge-001

CONFIGURATION CHECK:
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.jcfg
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.plugin.streaming.jcfg

NETWORK CONNECTIVITY:
curl -s http://localhost:8088/janus/info
curl -s http://localhost:8000/api/health
curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp

DEVICE MAPPINGS:
curl -s http://localhost:8000/api/devices/ | jq
curl -s http://localhost:8000/api/devices/05a9a734-f76d-4f45-9b0e-1e9c89b43e2c | jq
```

## 📋 **Configuration Checklist**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            CONFIGURATION CHECKLIST                              │
└─────────────────────────────────────────────────────────────────────────────────┘

BEFORE DEPLOYMENT:
□ docker-compose.asrock-edge.yml - Correct IP addresses
□ janus.jcfg - Valid syntax
□ janus.transport.websockets.jcfg - Port 8188
□ janus.transport.http.jcfg - Port 8088
□ janus.plugin.streaming.jcfg - Plugin enabled
□ janus.plugin.streaming.edge.jcfg - Valid RTSP URLs
□ vas/backend/app/core/constants.py - Device mappings
□ nginx-edge.conf - Proxy rules

AFTER DEPLOYMENT:
□ All services running
□ Janus API responding
□ Backend API responding
□ RTSP streams active
□ Frontend accessible
□ Video streams working
```

---

**This diagram provides a visual representation of the VAS system flow, making it easy to trace where failures occur and which configuration files to check.**

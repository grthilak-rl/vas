# VAS System Architecture Documentation

## Overview

The Video Analytics System (VAS) is a distributed edge computing platform designed for real-time camera feed processing and streaming. The architecture supports both local development (2-camera setup) and production edge computing deployment (6-camera ASRock units) with linear scalability.

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    VAS Distributed Architecture                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐  │
│  │   ASRock Unit   │    │   ASRock Unit   │    │  Central     │  │
│  │     001         │    │     002         │    │  Dashboard   │  │
│  │                 │    │                 │    │              │  │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │  │
│  │ │6 Cameras    │ │    │ │6 Cameras    │ │    │ │ API      │ │  │
│  │ │RTSP Feeds   │ │    │ │RTSP Feeds   │ │    │ │Aggregator│ │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └──────────┘ │  │
│  │        │        │    │        │        │    │      │       │  │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │  │
│  │ │Janus Gateway│ │    │ │Janus Gateway│ │    │ │ Web UI   │ │  │
│  │ │(WebRTC)     │ │    │ │(WebRTC)     │ │    │ │Dashboard │ │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └──────────┘ │  │
│  │        │        │    │        │        │    │      │       │  │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │      │       │  │
│  │ │YOLO AI      │ │    │ │YOLO AI      │ │    │      │       │  │
│  │ │Inference    │ │    │ │Inference    │ │    │      │       │  │
│  │ │(Intel Arc)  │ │    │ │(Intel Arc)  │ │    │      │       │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │      │       │  │
│  │        │        │    │        │        │    │      │       │  │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │      │       │  │
│  │ │Edge API     │ │────┼─│Edge API     │─┼────│──────┘       │  │
│  │ │Endpoints    │ │    │ │Endpoints    │ │    │              │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │              │  │
│  └─────────────────┘    └─────────────────┘    └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Janus WebRTC Gateway

**Purpose:** Real-time video streaming from RTSP cameras to web browsers

**Key Features:**
- Direct RTSP to WebRTC conversion
- H.264 passthrough (no transcoding required)
- Low-latency streaming (< 100ms)
- WebSocket and HTTP API support
- ICE/STUN for NAT traversal

**Configuration:**
- **Local Setup:** 2 cameras, basic configuration
- **Edge Setup:** 6 cameras, optimized for ASRock hardware

**Technology Stack:**
- C/C++ native implementation
- libnice for ICE connectivity
- libsrtp for secure RTP
- WebSocket transport layer

### 2. VAS Backend (FastAPI)

**Purpose:** Device management, authentication, and API orchestration

**Key Features:**
- RESTful API for device management
- JWT authentication system
- PostgreSQL database integration
- Device discovery and configuration
- Stream management coordination

**Endpoints:**
- `/api/devices/` - Camera device CRUD operations
- `/api/streams/` - Stream management
- `/auth/login` - Authentication
- `/health` - Health monitoring

**Technology Stack:**
- Python 3.11 with FastAPI framework
- SQLAlchemy ORM with PostgreSQL
- Pydantic for data validation
- Uvicorn ASGI server

### 3. VAS Frontend (React)

**Purpose:** Web-based user interface for camera monitoring

**Key Features:**
- Real-time video display using WebRTC
- Device management interface
- Stream control and monitoring
- Responsive design for multiple screen sizes

**Components:**
- `SimpleVideoPlayer.tsx` - WebRTC video player
- `Streams.tsx` - Camera streams page
- `Devices.tsx` - Device management
- `Dashboard.tsx` - System overview

**Technology Stack:**
- React 18 with TypeScript
- Modern WebRTC APIs
- CSS Grid for responsive layouts
- Serve for production deployment

### 4. Edge API Service

**Purpose:** Local edge unit management and central reporting

**Key Features:**
- Unit-specific configuration management
- Health and metrics reporting
- Camera stream configuration
- Central dashboard integration

**Endpoints:**
- `/health` - Unit health status
- `/metrics` - Performance metrics
- `/api/streams/configure` - Stream setup
- `/report_to_central_dashboard` - Central reporting

### 5. AI Inference Engine (Future)

**Purpose:** Real-time object detection using YOLO

**Planned Features:**
- Real-time YOLO object detection
- Intel Arc 140T GPU acceleration
- 1080p/30fps processing capability
- Object tracking and analytics

**Hardware Requirements:**
- Intel Arc 140T GPU (8 Xe cores)
- Intel NPU for AI acceleration
- 16GB system memory
- NVMe storage for model caching

## Deployment Architectures

### Local Development Setup

**Hardware:** Standard development machine
**Cameras:** 2 RTSP cameras
**Purpose:** Development, testing, and prototyping

```
┌─────────────────────────────────────────────────────────────┐
│                Local Development Setup                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Camera 1 (172.16.16.122) ──┐                              │
│                              │                              │
│  Camera 2 (172.16.16.123) ──┤                              │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Docker Host                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  Janus      │  │ VAS Backend │  │VAS Frontend │  │    │
│  │  │  Gateway    │  │  (FastAPI)  │  │  (React)    │  │    │
│  │  │ (WebRTC)    │  │             │  │             │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │         │                  │                │       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ PostgreSQL  │  │   Redis     │  │   Nginx     │  │    │
│  │  │  Database   │  │   Cache     │  │Reverse Proxy│  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                              │
│                              ▼                              │
│  Browser Access: http://localhost:3001                      │
│  Test Page: http://localhost:8082/test-camera-viewer.html   │
└─────────────────────────────────────────────────────────────┘
```

### Production Edge Setup

**Hardware:** ASRock iEP-7040E-024 units
**Cameras:** 6 RTSP cameras per unit
**Purpose:** Production deployment with AI capabilities

```
┌─────────────────────────────────────────────────────────────┐
│                ASRock Edge Unit Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cameras 1-6 (172.16.16.122-127) ──┐                       │
│                                     │                       │
│                                     ▼                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ASRock iEP-7040E-024 Unit                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │Janus Edge   │  │AI Inference │  │ Edge API    │  │    │
│  │  │(Optimized)  │  │(YOLO+Intel │  │ Service     │  │    │
│  │  │             │  │ Arc 140T)   │  │             │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │         │                  │                │       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │VAS Backend  │  │VAS Frontend │  │   Nginx     │  │    │
│  │  │   Edge      │  │    Edge     │  │    Edge     │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │         │                  │                │       │    │
│  │  ┌─────────────┐  ┌─────────────┐               │    │    │
│  │  │PostgreSQL   │  │   Redis     │               │    │    │
│  │  │   Edge      │  │   Edge      │               │    │    │
│  │  └─────────────┘  └─────────────┘               │    │    │
│  └─────────────────────────────────────────────────┼────┘    │
│                                                     │         │
│                                                     ▼         │
│  Central Dashboard API Reporting                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Video Streaming Flow

1. **RTSP Ingestion**
   - Cameras stream H.264 video via RTSP
   - Janus Gateway connects directly to camera RTSP endpoints
   - Authentication handled via digest auth

2. **WebRTC Conversion**
   - Janus converts RTSP to WebRTC without transcoding
   - ICE candidates generated for NAT traversal
   - SDP offer/answer negotiation with browsers

3. **Browser Delivery**
   - WebRTC streams delivered to browsers via WebSocket
   - Low-latency display in HTML5 video elements
   - Real-time synchronization maintained

### Control Flow

1. **Device Management**
   - Devices registered in PostgreSQL database
   - REST API provides CRUD operations
   - Frontend displays device status and controls

2. **Stream Configuration**
   - Janus plugin configuration maps devices to streams
   - Dynamic stream activation/deactivation
   - Resource allocation based on active streams

3. **Edge Coordination**
   - Edge API services report status to central dashboard
   - Health metrics aggregated across units
   - Configuration updates pushed to edge units

## Network Architecture

### Port Allocation

**Local Development:**
- 3001: VAS Frontend (React)
- 8000: VAS Backend (FastAPI)
- 8082: Test HTTP Server
- 8088: Janus HTTP API
- 8188: Janus WebSocket
- 5432: PostgreSQL Database
- 6379: Redis Cache
- 80: Nginx Reverse Proxy

**Edge Deployment:**
- 3000: VAS Frontend Edge
- 3001: Edge API Service
- 8000: VAS Backend Edge
- 8088: Janus HTTP API
- 8188: Janus WebSocket
- 5432: PostgreSQL Edge
- 6379: Redis Edge
- 80: Nginx Edge

### Network Modes

**Development:**
- Janus: `network_mode: host` (for ICE connectivity)
- Other services: Bridge network with explicit ports

**Production:**
- All services: Optimized networking for edge deployment
- GPU device mapping: `/dev/dri` for Intel Arc access

## Storage Architecture

### Database Schema

**Devices Table:**
- id (UUID primary key)
- name, location, description
- ip_address, port, rtsp_url
- device_type, manufacturer, model
- authentication credentials
- metadata (JSON)
- status, timestamps

**Future Extensions:**
- Analytics results storage
- Event logging and alerting
- Configuration versioning

### File Storage

**Local Development:**
- Docker volumes for persistent data
- Logs in `./logs/` directories
- Recordings in `./recordings/`

**Edge Deployment:**
- Optimized for limited edge storage
- Log rotation and cleanup
- Recording retention policies

## Scalability Design

### Horizontal Scaling

**Edge Units:**
- Each ASRock unit operates independently
- Linear scaling: add units without re-engineering
- Unit IDs (001, 002, 050) for identification

**Central Aggregation:**
- Central dashboard aggregates API endpoints
- No video processing at central level
- Only metadata and status information centralized

### Performance Characteristics

**Local Setup (2 cameras):**
- Target: 1080p/30fps per camera
- Latency: < 100ms end-to-end
- Concurrent viewers: 10+ per stream

**Edge Setup (6 cameras):**
- Target: 1080p/30fps per camera
- AI Inference: Real-time YOLO processing
- Hardware: Optimized for Intel Arc 140T
- Memory: 16GB system requirement

**Large Scale (300-500 cameras):**
- Deployment: 50-85 ASRock units
- Architecture: Distributed edge processing
- Central: API aggregation only
- Bandwidth: Minimal central requirements

## Security Architecture

### Authentication & Authorization

**Current Implementation:**
- JWT-based authentication
- Username/password login
- Session management
- Role-based access (planned)

**Camera Security:**
- RTSP digest authentication
- Encrypted credentials storage
- Network isolation options

### Network Security

**Local Development:**
- Container network isolation
- Local-only access by default
- HTTPS termination at Nginx

**Edge Deployment:**
- VPN connectivity options
- Firewall configuration
- Secure API endpoints
- Certificate management

## Monitoring & Observability

### Health Monitoring

**Service Health:**
- Docker container health checks
- Application-level health endpoints
- Database connectivity monitoring
- Stream availability checking

**Performance Metrics:**
- CPU/GPU utilization
- Memory usage patterns
- Network bandwidth consumption
- Stream quality metrics

### Logging Architecture

**Application Logs:**
- Structured JSON logging
- Centralized log aggregation
- Error tracking and alerting
- Performance monitoring

**Janus Logs:**
- WebRTC connection logs
- Stream quality reports
- Error diagnostics
- Performance profiling

## Future Enhancements

### AI Integration

**YOLO Object Detection:**
- Real-time inference on Intel Arc 140T
- Object tracking and analytics
- Event-driven alerting
- Metadata enrichment

**Advanced Analytics:**
- Behavior analysis
- Anomaly detection
- Predictive analytics
- Integration with business systems

### System Enhancements

**Auto-scaling:**
- Dynamic resource allocation
- Load-based scaling decisions
- Automated failover mechanisms
- Performance optimization

**Enterprise Features:**
- Multi-tenant architecture
- Advanced user management
- Audit logging
- Compliance reporting

## Deployment Strategy

### Development Workflow

1. **Local Development**
   ```bash
   docker-compose up --build -d
   ```

2. **Regression Testing**
   ```bash
   ./test-local-regression.sh
   ```

3. **Edge Deployment**
   ```bash
   ./deploy-edge.sh --unit-id 001
   ```

### Production Deployment

1. **Hardware Preparation**
   - ASRock unit setup and configuration
   - Network connectivity establishment
   - Camera installation and configuration

2. **Software Deployment**
   - Docker and dependencies installation
   - VAS system deployment via script
   - Configuration validation and testing

3. **Monitoring Setup**
   - Health check configuration
   - Performance monitoring activation
   - Alert system configuration

This architecture provides a robust, scalable foundation for real-time video analytics at the edge while maintaining centralized oversight and management capabilities.

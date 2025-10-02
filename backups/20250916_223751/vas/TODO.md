# VAS Project TODO

This file tracks all major tasks for the Video Aggregation Service (VAS) project across all phases. ✅ = completed, ⏳ = in progress, ❌ = not started

---

## Phase 1: Backend Foundation ✅

### Core Infrastructure
- [x] Project structure and repository setup
- [x] FastAPI backend application scaffold
- [x] PostgreSQL database integration
- [x] SQLAlchemy ORM models for devices
- [x] Alembic migrations for schema management
- [x] Redis cache integration
- [x] Docker and Docker Compose setup
- [x] Environment variable and config management

### Authentication & Security
- [x] JWT authentication and role-based access control
- [x] User authentication endpoints (login, token)
- [x] Encrypted credential storage

### API Development
- [x] Device CRUD API endpoints (create, read, update, delete)
- [x] Device listing with pagination and filtering
- [x] Device validation (RTSP stream validation)
- [x] Device discovery (network scan for RTSP devices)
- [x] Device metadata and tags (JSON fields)
- [x] Device status monitoring endpoint
- [x] Health check endpoint
- [x] Error handling and custom exception responses
- [x] API documentation (Swagger/OpenAPI)

### Testing & Documentation
- [x] Sample data scripts (add_sample_devices, add_live_cameras)
- [x] Comprehensive API test scripts
- [x] Serialization/deserialization fixes for UUID and JSON fields
- [x] Backend README and root README updates

### Project Organization
- [x] Project reorganization: move all backend files to backend/
- [x] Create comprehensive TODO.md for project tracking

---

## Phase 1.1: Backend Enhancements ✅

- [x] Add background scheduler for device status monitoring (periodically ping RTSP streams and update status in Redis)
- [x] Encrypt device credentials (RTSP username/password) in the database using AES or integrate HashiCorp Vault
- [x] Add `/api/metrics` endpoint for operational stats (uptime, API requests count, error rates)
- [ ] Enhance device discovery with parallelized network scanning (threading or asyncio)

---

## Phase 2: WebRTC Enablement & Janus Integration ✅

### Janus Gateway Deployment
- [x] Setup Janus Gateway Docker container with WebSocket and REST plugins
- [x] Configure Janus for RTSP input streams via janus.plugin.streaming
- [x] Expose necessary ports (WebSocket 8188, HTTP API 8088, RTP/RTCP 20000-25000)
- [x] Configure firewall for UDP RTP/RTCP port ranges
- [ ] Enable HTTPS for secure streams (optional)

### RTSP to WebRTC Integration
- [x] Implement backend logic to register cameras as Janus mountpoints
- [x] Auto-register new cameras as Janus mountpoints
- [x] Remove mountpoints if cameras are removed
- [x] Health-check all mountpoints periodically
- [x] Map camera_id -> RTSP URL -> Janus mountpoint

### API Layer Enhancements
- [x] Add GET /api/streams endpoint (List all available camera streams with status)
- [x] Add POST /api/streams/{id}/start endpoint (Start a stream)
- [x] Add POST /api/streams/{id}/stop endpoint (Stop a stream)
- [x] Add GET /api/streams/{id}/status endpoint (Get current health of a stream)
- [x] Integrate stream management with existing device APIs

### Health Monitoring & Auto-Recovery ✅
- [x] Implement stream health monitoring service
- [x] Check if Janus mountpoint is active
- [x] Check if RTSP feed is alive
- [x] Auto-reconnect Janus mountpoints on failures
- [x] Log stream errors, user connections, WebSocket errors
- [x] Implement retry/backoff mechanisms

### Scalability & Performance
- [x] Support multiple concurrent users viewing same camera feed
- [x] Reuse Janus mountpoints instead of creating new ones per user
- [ ] Minimize server load through efficient mountpoint management
- [ ] Implement connection pooling and resource management

### Testing & Documentation
- [ ] Write unit and integration tests for stream APIs
- [x] Test RTSP to Janus integration with public streams
- [x] Test WebRTC browser streaming (Chrome/Firefox)
- [ ] Test multiple browser tabs watching same camera
- [ ] Test edge cases (camera feed drops, Janus restart)
- [ ] Document Janus setup and APIs

---

## Phase 3: Advanced Frontend Web Application ⏳

### Core Frontend
- [x] React/Vue.js frontend application setup
- [x] Responsive UI design system
- [x] Component library for video management
- [x] State management (Redux/Vuex)

### Device Management UI
- [x] Device dashboard and overview
- [x] Device CRUD operations interface
- [ ] Device discovery and scanning interface
- [ ] Device configuration and settings
- [x] Real-time device status monitoring

### Authentication & User Management
- [x] Login/logout interface
- [ ] User profile management
- [x] Role-based UI access control
- [ ] Password reset functionality

### Video Preview & Control
- [x] Video stream preview components
- [x] Basic video controls (play, pause, stop)
- [ ] Video quality selection
- [ ] Screenshot capture functionality

### Advanced Features
- [ ] Device grouping and organization
- [ ] Search and filtering interface
- [x] Bulk operations (delete, update multiple devices)
- [ ] Export/import device configurations

---

## Phase 4: Advanced Analytics and AI ❌

### Video Analytics
- [ ] Motion detection and alerts
- [ ] Object detection and recognition
- [ ] Face detection and recognition
- [ ] License plate recognition
- [ ] People counting

### Data Analytics
- [ ] Usage analytics dashboard
- [ ] Performance metrics and monitoring
- [ ] Historical data analysis
- [ ] Custom reporting system

### AI/ML Integration
- [ ] Machine learning model integration
- [ ] Predictive maintenance alerts
- [ ] Anomaly detection
- [ ] Automated video tagging

---

## Phase 5: Mobile Applications ❌

### Mobile App Development
- [ ] React Native or Flutter mobile app
- [ ] Cross-platform compatibility (iOS/Android)
- [ ] Mobile-optimized video streaming
- [ ] Push notifications for alerts

### Mobile Features
- [ ] Device monitoring on mobile
- [ ] Video preview and playback
- [ ] Quick device configuration
- [ ] Offline mode support

---

## DevOps & Infrastructure ❌

### Deployment & Scaling
- [ ] Production deployment setup
- [ ] Load balancing configuration
- [ ] Auto-scaling implementation
- [ ] Monitoring and alerting

### Security & Compliance
- [ ] SSL/TLS certificate management
- [ ] Security audit and penetration testing
- [ ] GDPR compliance features
- [ ] Data encryption at rest

### Performance & Monitoring
- [ ] Application performance monitoring
- [ ] Database performance optimization
- [ ] Log aggregation and analysis
- [ ] Backup and disaster recovery

---

## Documentation & Support ❌

### Documentation
- [ ] API documentation updates
- [ ] User guides and tutorials
- [ ] Developer documentation
- [ ] Deployment guides

### Support & Maintenance
- [ ] Bug tracking and issue management
- [ ] User support system
- [ ] Regular security updates
- [ ] Performance optimization

---

**How to use:**
- Mark completed tasks with `[x]`
- Mark in-progress tasks with `[⏳]`
- Mark not started tasks with `[ ]`
- Add new tasks as needed

**Current Status:**
- **Phase 1**: ✅ Complete
- **Phase 1.1**: ✅ Complete (except parallelized discovery)
- **Phase 2**: ✅ Complete
- **Phase 3**: ⏳ In Progress (Core features complete)
- **Phase 4**: ❌ Not started
- **Phase 5**: ❌ Not started

**Next Steps:**
1. Complete remaining Phase 2 tasks (frontend WebRTC player)
2. Begin Phase 3 frontend development
3. Consider Phase 4 analytics features
4. Plan Phase 5 mobile applications 
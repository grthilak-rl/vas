# Cross-Server Deployment Guide
## VAS + Ruth-AI Monitor on Different Servers

This guide explains how to deploy VAS and Ruth-AI Monitor on separate servers while maintaining WebRTC camera feed functionality.

## 🏗️ Architecture Overview

```
┌─────────────────────┐    ┌─────────────────────┐
│   Ruth-AI Monitor   │    │        VAS          │
│     Server A        │    │     Server B        │
│                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │   Frontend    │  │    │  │   Backend     │  │
│  │   (Port 3004) │  │    │  │   (Port 8000) │  │
│  └───────────────┘  │    │  └───────────────┘  │
│                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │   Backend     │  │    │  │   Janus       │  │
│  │   (Port 3005) │  │    │  │   (Port 8188) │  │
│  └───────────────┘  │    │  └───────────────┘  │
└─────────────────────┘    └─────────────────────┘
         │                           │
         └─────────── HTTP/WS ───────┘
```

## 🔧 Configuration Requirements

### 1. VAS Server (Server B) Configuration

**Required Services:**
- VAS Backend API (Port 8000)
- Janus WebRTC Gateway (Port 8188)
- PostgreSQL Database
- Redis Cache

**Network Access:**
- Port 8000: HTTP API access from Ruth-AI Monitor
- Port 8188: WebSocket access from client browsers
- Port 5432: PostgreSQL (internal only)
- Port 6379: Redis (internal only)

### 2. Ruth-AI Monitor Server (Server A) Configuration

**Environment Variables:**
```bash
# VAS Integration URLs
VITE_VAS_API_URL=http://10.30.250.245:8000/api
VITE_VAS_WS_URL=ws://10.30.250.245:8188/janus

# Ruth-AI Monitor Services
VITE_API_URL=http://RUTH_SERVER_IP:3005/api
VITE_WS_URL=ws://RUTH_SERVER_IP:3005
```

## 🚀 Deployment Steps

### Step 1: Deploy VAS (Server B)

```bash
# On VAS server
cd /home/atgin-rnd-ubuntu/vas

# Ensure VAS is running
./deploy-edge.sh

# Verify services are running
docker ps | grep -E "(vas-backend|janus-edge)"
```

**Expected Output:**
```
vas-backend-edge-001    Running on port 8000
janus-edge-001          Running on port 8188
```

### Step 2: Deploy Ruth-AI Monitor (Server A)

```bash
# On Ruth-AI Monitor server
cd /path/to/ruth-ai-monitor

# Set environment variables
export VITE_VAS_API_URL=http://10.30.250.245:8000/api
export VITE_VAS_WS_URL=ws://10.30.250.245:8188/janus

# Deploy services
docker-compose up -d

# Verify services are running
docker ps | grep ruth
```

### Step 3: Network Connectivity Test

**From Ruth-AI Monitor Server:**
```bash
# Test VAS API connectivity
curl http://10.30.250.245:8000/api/health

# Test Janus WebSocket connectivity
curl -I http://10.30.250.245:8188/janus
```

**From Client Browser:**
```bash
# Test WebRTC WebSocket
# Open browser console and run:
new WebSocket('ws://10.30.250.245:8188/janus')
```

## 🔍 Troubleshooting

### Common Issues

**1. CORS Errors**
```
Access to fetch at 'http://VAS_SERVER_IP:8000/api/auth/login-json' 
from origin 'http://RUTH_SERVER_IP:3004' has been blocked by CORS policy
```

**Solution:** VAS CORS is already configured to allow all origins (`["*"]`). If you see CORS errors, check:
- VAS backend is running on correct port
- Network connectivity between servers
- Firewall rules

**2. WebSocket Connection Failed**
```
WebSocket connection to 'ws://10.30.250.245:8188/janus' failed
```

**Solution:** Check:
- Janus is running on port 8188
- Firewall allows WebSocket connections
- Network routing between servers

**3. Camera Discovery Fails**
```
Failed to fetch cameras: Network Error
```

**Solution:** Check:
- VAS API is accessible from Ruth-AI Monitor server
- Authentication is working
- Database has camera data

### Debug Commands

**Check VAS Services:**
```bash
# On VAS server
docker logs vas-backend-edge-001 --tail 20
docker logs janus-edge-001 --tail 20
```

**Check Ruth-AI Monitor Services:**
```bash
# On Ruth-AI Monitor server
docker logs ruth-monitor-web --tail 20
docker logs ruth-monitor-api --tail 20
```

**Test API Endpoints:**
```bash
# Test VAS health
curl http://10.30.250.245:8000/api/health

# Test VAS authentication
curl -X POST http://10.30.250.245:8000/api/auth/login-json \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test camera discovery
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://10.30.250.245:8000/api/devices
```

## 🔒 Security Considerations

### Production Deployment

**1. Restrict CORS Origins**
```python
# In VAS backend config.py
allowed_hosts: List[str] = Field(
    default=[
        "http://RUTH_SERVER_IP:3004",
        "https://your-domain.com"
    ], 
    env="ALLOWED_HOSTS"
)
```

**2. Use HTTPS/WSS**
```bash
# For production
VITE_VAS_API_URL=https://10.30.250.245:8000/api
VITE_VAS_WS_URL=wss://10.30.250.245:8188/janus
```

**3. Firewall Rules**
```bash
# Allow only necessary ports
# VAS Server: 8000 (HTTP), 8188 (WebSocket)
# Ruth-AI Monitor Server: 3004 (HTTP), 3005 (API)
```

## ✅ Verification Checklist

- [ ] VAS backend accessible from Ruth-AI Monitor server
- [ ] Janus WebSocket accessible from client browsers
- [ ] Camera discovery working in Ruth-AI Monitor
- [ ] WebRTC streams displaying in Ruth-AI Monitor
- [ ] No CORS errors in browser console
- [ ] No WebSocket connection errors
- [ ] Authentication working between services

## 🎯 Expected Behavior

When properly configured:
1. **Ruth-AI Monitor** fetches camera list from VAS API
2. **Client browsers** connect directly to Janus WebSocket on VAS server
3. **WebRTC streams** flow from VAS → Client browsers
4. **AI processing** happens on Ruth-AI Monitor server
5. **Violation detection** works with live VAS camera feeds

The cross-server deployment maintains full functionality while allowing independent scaling and management of each service.

# VAS Development Safety Guide

## 🚨 **CRITICAL: Preventing Configuration Drift**

This guide ensures we never lose our working VAS setup when adding new features. **READ THIS BEFORE MAKING ANY CHANGES.**

## 🎯 **Current Working Configuration (DO NOT CHANGE)**

### **Core Components**
- **Docker Compose**: `docker-compose.yml` (local development)
- **Janus Config**: `janus.plugin.streaming.jcfg` (2 live cameras)
- **Janus Image**: Custom build from `./janus/Dockerfile`
- **Base Image**: Ubuntu 18.04 with libcurl 7.87.0
- **RTSP Auth**: Digest method (requires libcurl 7.87.0)

### **Live Cameras**
- **Camera 1**: `rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp` (Office)
- **Camera 2**: `rtsp://root:G3M13m0b@172.16.16.123/live1s1.sdp` (Lobby)

## ⚠️ **NEVER DO THESE THINGS**

### **❌ NEVER Change These Files**
- `janus/Dockerfile` - Custom build with libcurl 7.87.0
- `janus/config/janus.plugin.streaming.jcfg` - Working 2-camera config
- `docker-compose.yml` - Working local setup
- `janus/config/janus.jcfg` - Main Janus configuration

### **❌ NEVER Use These Images**
- `canyan/janus-gateway:latest` - 2 years old, missing libcurl 7.87.0
- Any pre-built Janus images - They don't have our custom libcurl
- Different base images - Ubuntu 18.04 is stable

### **❌ NEVER Change These Settings**
- RTSP authentication method (must be digest)
- libcurl version (must be 7.87.0)
- Network mode for Janus (must be host)
- Port configurations (8088, 8188)

## ✅ **SAFE DEVELOPMENT WORKFLOW**

### **Step 1: Backup Before Changes**
```bash
# Create complete backup of working state
./backup-config.sh

# Verify backup was created
ls -la backups/latest-working/
```

### **Step 2: Test Current Setup**
```bash
# Run regression tests to ensure everything works
./test-local-regression.sh

# Check Janus is using correct image
docker inspect janus_gateway | jq -r '.[0].Config.Image'
# Should return: vas_janus_gateway (custom build)
```

### **Step 3: Make Changes Safely**
```bash
# Start with small, incremental changes
# Test each change before proceeding
# Use feature branches for major changes
```

### **Step 4: Test After Changes**
```bash
# Run regression tests again
./test-local-regression.sh

# Check video feeds still work
curl -s http://localhost:8088/janus/info | grep -q "janus"
```

### **Step 5: If Something Breaks**
```bash
# Quick recovery from backup
./recover.sh latest

# Or manual recovery
docker-compose down
docker-compose up --build -d
```

## 🔧 **Development Environment Setup**

### **Local Development (Recommended)**
```bash
# Use this for all development work
docker-compose up --build -d

# Access points:
# Frontend: http://localhost:3001
# Backend API: http://localhost:8000/docs
# Janus API: http://localhost:8088/janus/info
# Test Page: http://localhost:8082/test-camera-viewer.html
```

### **Testing New Features**
```bash
# 1. Backup current state
./backup-config.sh

# 2. Make changes in feature branch
git checkout -b feature/new-feature

# 3. Test changes
./test-local-regression.sh

# 4. If tests pass, merge to main
# 5. If tests fail, revert changes
```

## 🚨 **Emergency Recovery Procedures**

### **If Video Feeds Stop Working**
```bash
# 1. Check Janus container status
docker-compose ps janus-gateway

# 2. Check Janus logs
docker-compose logs janus-gateway | tail -20

# 3. Verify Janus image
docker inspect janus_gateway | jq -r '.[0].Config.Image'

# 4. If wrong image, rebuild
docker-compose build janus-gateway
docker-compose up -d janus-gateway
```

### **If Configuration Gets Corrupted**
```bash
# 1. Stop all services
docker-compose down

# 2. Recover from backup
./recover.sh latest

# 3. Start services
docker-compose up -d

# 4. Verify everything works
./test-local-regression.sh
```

### **If Database Issues Occur**
```bash
# 1. Check database container
docker-compose ps db

# 2. Check database logs
docker-compose logs db

# 3. Restart database
docker-compose restart db

# 4. Re-populate devices if needed
cd vas/backend && python3 add_sample_devices.py
```

## 📋 **Pre-Development Checklist**

Before starting any development work:

- [ ] **Backup created**: `./backup-config.sh` completed
- [ ] **Tests passing**: `./test-local-regression.sh` shows all green
- [ ] **Janus image correct**: Custom build, not canyan/janus-gateway
- [ ] **Video feeds working**: Both cameras showing video
- [ ] **API responding**: Backend and Janus APIs accessible
- [ ] **Feature branch created**: Working on separate branch

## 📋 **Post-Development Checklist**

After making changes:

- [ ] **Tests still passing**: `./test-local-regression.sh` shows all green
- [ ] **Video feeds working**: Both cameras still showing video
- [ ] **No configuration drift**: Janus image and configs unchanged
- [ ] **API responding**: All endpoints still accessible
- [ ] **Backup updated**: New backup created with working changes

## 🔍 **Diagnostic Commands**

### **Check System Health**
```bash
# All services status
docker-compose ps

# Janus health
curl -s http://localhost:8088/janus/info | jq

# Backend health
curl -s http://localhost:8000/health | jq

# Database health
docker-compose exec db pg_isready -U vas_user -d vas_db
```

### **Check Video Streams**
```bash
# Test RTSP streams directly
curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp
curl -s rtsp://root:G3M13m0b@172.16.16.123/live1s1.sdp

# Check Janus streaming plugin
curl -s http://localhost:8088/janus/streaming | jq
```

### **Check Configuration**
```bash
# Verify Janus config files
docker exec janus_gateway cat /opt/janus/etc/janus/janus.plugin.streaming.jcfg

# Check environment variables
docker exec janus_gateway env | grep JANUS
```

## 📚 **Key Files to Monitor**

### **Critical Configuration Files**
- `janus/Dockerfile` - Janus build configuration
- `janus/config/janus.plugin.streaming.jcfg` - Stream definitions
- `janus/config/janus.jcfg` - Main Janus config
- `docker-compose.yml` - Service definitions
- `vas/backend/app/core/constants.py` - Device mappings

### **Backup Files**
- `backups/latest-working/` - Latest working configuration
- `backups/YYYYMMDD_HHMMSS/` - Timestamped backups

### **Test Files**
- `test-local-regression.sh` - Regression test script
- `test-camera-viewer.html` - HTML test page
- `webrtc-api-test.html` - WebRTC test page

## 🎯 **Best Practices**

### **Development**
1. **Always backup before changes**
2. **Use feature branches for major changes**
3. **Test incrementally**
4. **Keep changes small and focused**
5. **Document any configuration changes**

### **Testing**
1. **Run regression tests before and after changes**
2. **Test video feeds manually**
3. **Check all API endpoints**
4. **Verify database integrity**
5. **Test on different browsers**

### **Recovery**
1. **Know your recovery procedures**
2. **Keep backups current**
3. **Test recovery procedures**
4. **Have rollback plans**
5. **Document any issues and solutions**

## 🚨 **Red Flags - Stop Immediately**

If you see any of these, **STOP** and investigate:

- ❌ **Janus container won't start**
- ❌ **Video feeds show "No Signal"**
- ❌ **WebSocket connection errors**
- ❌ **RTSP authentication failures**
- ❌ **Database connection errors**
- ❌ **API endpoints returning 500 errors**
- ❌ **Wrong Janus image being used**
- ❌ **Configuration files missing or corrupted**

## 📞 **Emergency Contacts**

- **System Admin**: [Your contact info]
- **Development Team**: [Team contact info]
- **Backup Location**: `backups/latest-working/`
- **Recovery Script**: `./recover.sh latest`

## 📝 **Change Log**

- **2025-01-XX**: Created safety guide
- **2025-01-XX**: Added emergency recovery procedures
- **2025-01-XX**: Updated diagnostic commands

---

## 🎯 **Remember**

**The goal is to add features without breaking the working system. When in doubt, backup first, test thoroughly, and recover quickly if needed.**

**This working setup took significant time to establish. Don't let configuration drift waste that effort again.**

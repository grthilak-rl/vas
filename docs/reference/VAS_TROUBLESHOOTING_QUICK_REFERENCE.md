# VAS Troubleshooting Quick Reference

## 🚨 **Common Issues & Quick Fixes**

### **"No video feed"**
**Symptoms**: Black video, "Remote track muted", "Removing remote track"
**Quick Check**: `docker logs janus-edge-001 | grep -E "\[stream-[12]\]"`
**Fix**: Check `janus.plugin.streaming.edge.jcfg` RTSP URLs and authentication

### **"Connection refused"**
**Symptoms**: `net::ERR_CONNECTION_REFUSED`, API calls fail
**Quick Check**: `docker ps | grep -E "(janus|vas-backend|nginx)"`
**Fix**: Check service status and port configurations

### **"No proxy mountpoint configured"**
**Symptoms**: Backend error when starting stream
**Quick Check**: `curl -s http://localhost:8000/api/devices/ | jq`
**Fix**: Check `vas/backend/app/core/constants.py` device mappings

### **"Authentication failed"**
**Symptoms**: 401 errors, login failures
**Quick Check**: RTSP credentials in `janus.plugin.streaming.edge.jcfg`
**Fix**: Verify RTSP authentication parameters

### **"Janus library not loaded"**
**Symptoms**: `TypeError: v is not a constructor`, WebRTC errors
**Quick Check**: Browser console for Janus errors
**Fix**: Check `vas/frontend/public/index.html` Janus script tags

## 🔍 **Diagnostic Commands**

### **Service Status**
```bash
# Check all services
docker-compose -f docker-compose.asrock-edge.yml ps

# Check specific service
docker logs janus-edge-001
docker logs vas-backend-edge-001
docker logs nginx-edge-001
```

### **Configuration Check**
```bash
# Check Janus configuration
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.jcfg
docker exec janus-edge-001 cat /opt/janus/etc/janus/janus.plugin.streaming.jcfg

# Check device mappings
grep -A 10 "DEVICE_TO_MOUNTPOINT_MAP" vas/backend/app/core/constants.py
```

### **Network Connectivity**
```bash
# Check Janus API
curl -s http://localhost:8088/janus/info

# Check backend API
curl -s http://localhost:8000/api/health

# Check RTSP streams
curl -s rtsp://root:G3M13m0b@172.16.16.122/live1s1.sdp
```

### **Device Operations**
```bash
# List devices
curl -s http://localhost:8000/api/devices/ | jq

# Check specific device
curl -s http://localhost:8000/api/devices/05a9a734-f76d-4f45-9b0e-1e9c89b43e2c | jq
```

## 📋 **Configuration File Checklist**

### **Critical Files**
- `docker-compose.asrock-edge.yml` - Service definitions
- `janus.jcfg` - Main Janus configuration
- `janus.transport.websockets.jcfg` - WebSocket transport
- `janus.transport.http.jcfg` - HTTP API
- `janus.plugin.streaming.jcfg` - Streaming plugin
- `janus.plugin.streaming.edge.jcfg` - RTSP streams
- `vas/backend/app/core/constants.py` - Device mappings
- `nginx-edge.conf` - Proxy configuration

### **Quick Validation**
```bash
# Check syntax
docker-compose -f docker-compose.asrock-edge.yml config

# Check Janus config
docker exec janus-edge-001 janus --config=/opt/janus/etc/janus/janus.jcfg --check-config

# Check Nginx config
docker exec nginx-edge-001 nginx -t
```

## 🔧 **Recovery Procedures**

### **Quick Recovery**
```bash
# Stop services
docker-compose -f docker-compose.asrock-edge.yml down

# Rebuild Janus
docker-compose -f docker-compose.asrock-edge.yml build janus-edge

# Start services
docker-compose -f docker-compose.asrock-edge.yml up -d

# Verify
./deploy-edge.sh
```

### **From Backup**
```bash
# List backups
ls -la backups/

# Recover from latest
./recover.sh latest --dry-run  # Preview
./recover.sh latest            # Execute
```

### **Emergency Reset**
```bash
# Stop all services
docker-compose -f docker-compose.asrock-edge.yml down

# Remove containers and images
docker system prune -a

# Restore from backup
./recover.sh backups/latest-working --force
```

## 🎯 **Failure Point Identification**

### **Startup Failures**
1. **Docker Compose**: Check `docker-compose.asrock-edge.yml`
2. **Database**: Check connection strings and IP addresses
3. **Janus**: Check configuration files and custom build
4. **Backend**: Check database and Redis connections
5. **Nginx**: Check proxy configuration

### **Runtime Failures**
1. **Frontend**: Check Janus libraries and WebRTC code
2. **Authentication**: Check RTSP credentials and JWT handling
3. **Video Streams**: Check RTSP URLs and device mappings
4. **API Calls**: Check backend connectivity and schemas

## 📊 **Health Check Commands**

### **System Health**
```bash
# All services running
docker ps | grep -E "(janus|vas-backend|nginx|edge-db|edge-redis)"

# All ports open
netstat -tlnp | grep -E "(80|8000|8088|8188|5432|6379)"

# All APIs responding
curl -s http://localhost:8088/janus/info | jq
curl -s http://localhost:8000/api/health | jq
```

### **Stream Health**
```bash
# RTSP streams active
docker logs janus-edge-001 | grep -E "\[stream-[12]\]"

# WebRTC connections
docker logs janus-edge-001 | grep -i "webrtc"

# Video data flowing
docker logs janus-edge-001 | grep -i "video"
```

## 🚀 **Prevention Checklist**

### **Before Changes**
- [ ] Create backup: `./backup-config.sh`
- [ ] Test in dry-run mode: `./recover.sh latest --dry-run`
- [ ] Document changes in commit messages

### **After Changes**
- [ ] Verify deployment: `./deploy-edge.sh`
- [ ] Check all services: `docker ps`
- [ ] Test video streams: Open browser
- [ ] Create new backup: `./backup-config.sh`

### **Regular Maintenance**
- [ ] Weekly backups
- [ ] Monitor service logs
- [ ] Check disk space
- [ ] Update documentation

---

**This quick reference provides immediate access to diagnostic commands and fixes for common VAS issues.**

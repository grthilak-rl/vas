# VAS Deployment Guide - Single Source of Truth

## 🎯 **Working Configuration (Verified)**

### **Critical Components**
- **Janus**: Custom build from source (NOT canyan/janus-gateway)
- **libcurl**: Version 7.87.0 (built from source)
- **RTSP Auth**: Digest authentication with specific parameters
- **Network**: Host networking for optimal performance

### **Docker Images**
```bash
# ✅ WORKING (Custom Build)
janus-edge: vas_janus-edge (custom build from ./janus/Dockerfile)

# ❌ BROKEN (Pre-built)
janus-edge: canyan/janus-gateway:latest (2 years old, missing libcurl 7.87.0)
```

### **Critical Configuration Files**
1. **Janus RTSP Config**: `janus/config/janus.plugin.streaming.jcfg`
2. **Database URLs**: Must use correct IP addresses for host networking
3. **Authentication**: Digest method with specific user/password

## 🚀 **One-Command Deployment**

### **Deploy Everything**
```bash
# This script deploys the EXACT working configuration
./deploy-edge.sh
```

### **Verify Deployment**
```bash
# Check all services are running
docker ps | grep -E "(janus-edge|vas-backend|edge-db)"

# Check RTSP streams are active
docker logs janus-edge-001 | grep -E "(stream-1|stream-2)" | tail -5

# Check backend API
curl -s http://localhost:8000/api/health | jq
```

## 🔧 **Troubleshooting Checklist**

### **If Video Feeds Don't Work**
1. **Check Janus Image**: Must be `vas_janus-edge` (custom build)
2. **Check RTSP Auth**: Must be digest method
3. **Check Database IP**: Must be `172.21.0.3` for host networking
4. **Check Streams**: Must see `[stream-1]` and `[stream-2]` in logs

### **Common Mistakes**
- ❌ Using `canyan/janus-gateway:latest` instead of custom build
- ❌ Wrong database IP (`172.21.0.2` instead of `172.21.0.3`)
- ❌ Missing RTSP authentication parameters
- ❌ Using basic auth instead of digest

## 📋 **Configuration Backup**

All working configurations are stored in:
- `janus/config/` - Janus configuration files
- `docker-compose.asrock-edge.yml` - Service definitions
- `deploy-edge.sh` - Deployment script

## 🔄 **Recovery Process**

If something breaks:
1. Stop all services: `docker-compose -f docker-compose.asrock-edge.yml down`
2. Rebuild custom Janus: `docker-compose -f docker-compose.asrock-edge.yml build janus-edge`
3. Start services: `docker-compose -f docker-compose.asrock-edge.yml up -d`
4. Verify: Check logs for `[stream-1]` and `[stream-2]`

## 📝 **Change Log**

- **2025-09-17**: Fixed RTSP authentication by switching to custom Janus build
- **2025-09-17**: Fixed database connection IP for host networking
- **2025-09-17**: Verified working configuration with libcurl 7.87.0

## 🔍 **Quick Diagnostics**

### **Check Janus Image**
```bash
docker inspect janus-edge-001 | jq -r '.[0].Config.Image'
# Should return: vas_janus-edge
```

### **Check RTSP Streams**
```bash
docker logs janus-edge-001 | grep -E "\[stream-[12]\]" | tail -5
# Should show active streams
```

### **Check Database Connection**
```bash
docker logs vas-backend-edge-001 | grep -i "database"
# Should show successful connection
```

### **Check Backend API**
```bash
curl -s http://localhost:8000/api/health | jq
# Should return: {"status": "healthy"}
```

## 🚨 **Emergency Recovery**

If everything breaks and you need to start fresh:

1. **Stop all services**:
   ```bash
   docker-compose -f docker-compose.asrock-edge.yml down
   ```

2. **Remove all containers and images**:
   ```bash
   docker system prune -a
   ```

3. **Restore from backup**:
   ```bash
   ./recover.sh backups/latest-working
   ```

4. **Verify deployment**:
   ```bash
   ./deploy-edge.sh
   ```

## 📚 **Additional Resources**

- **Janus Configuration**: `janus/config/janus.plugin.streaming.jcfg`
- **Docker Compose**: `docker-compose.asrock-edge.yml`
- **Deployment Script**: `deploy-edge.sh`
- **Backup Script**: `backup-config.sh`
- **Recovery Script**: `recover.sh`

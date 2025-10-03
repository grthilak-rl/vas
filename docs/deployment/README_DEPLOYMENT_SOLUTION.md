# VAS Deployment Solution - Preventing Configuration Drift

## 🎯 **Problem Solved**

This solution addresses the recurring issue of having to debug the same WebRTC streaming problems repeatedly. The root cause was **configuration drift** - the system would work, then break due to:

1. **Wrong Docker images** (canyan vs custom-built Janus)
2. **Scattered configuration files** across different locations
3. **No single source of truth** for the working setup
4. **Manual fixes** that get lost over time

## 🛠️ **Solution Implemented**

### **1. DEPLOYMENT_GUIDE.md**
- **Single source of truth** for working configuration
- **Critical components** documented (Janus custom build, libcurl 7.87.0, RTSP digest auth)
- **Troubleshooting checklist** for common issues
- **Quick diagnostics** commands
- **Emergency recovery** procedures

### **2. Enhanced deploy-edge.sh**
- **Automated verification** of deployment integrity
- **Checks Janus image** (must be `vas_janus-edge`)
- **Verifies RTSP streams** are active
- **Validates backend API** health
- **Prevents deployment** if wrong configuration detected

### **3. backup-config.sh**
- **Complete configuration backup** of working state
- **Docker state information** (images, containers, networks)
- **System information** (OS, network, disk, memory)
- **Service logs** for debugging
- **Recovery instructions** in manifest
- **Latest working link** for easy access

### **4. recover.sh**
- **Quick recovery** from any backup
- **Emergency backup** before recovery
- **Dry-run mode** to preview changes
- **Automatic verification** after recovery
- **Support for 'latest'** shortcut

## 🚀 **Usage**

### **Deploy with Verification**
```bash
./deploy-edge.sh
# Automatically verifies all critical components
```

### **Create Working Backup**
```bash
./backup-config.sh
# Creates complete backup with manifest
```

### **Quick Recovery**
```bash
./recover.sh latest --dry-run  # Preview
./recover.sh latest            # Recover
```

### **Emergency Recovery**
```bash
./recover.sh backups/20250917_130626 --force
```

## 🔍 **Verification Process**

The enhanced deployment script now automatically verifies:

1. **Janus Image**: Must be `vas_janus-edge` (custom build)
2. **RTSP Streams**: Must see `[stream-1]` and `[stream-2]` in logs
3. **Backend API**: Must return healthy status
4. **Database Connection**: Must be connected
5. **Redis Connection**: Must be connected

## 📋 **Backup Contents**

Each backup includes:
- **Configuration files** (Janus, Docker Compose, Nginx, deployment script)
- **Docker state** (images, containers, networks, volumes)
- **System information** (OS, network, disk, memory)
- **Service logs** (Janus, backend, database, Redis, Nginx)
- **Recovery instructions** (manifest file)

## 🔄 **Recovery Process**

1. **Stop current services**
2. **Create emergency backup** (safety net)
3. **Restore configuration files**
4. **Rebuild custom Janus image**
5. **Start services**
6. **Verify recovery** (same checks as deployment)

## 🎉 **Benefits**

### **Prevents Configuration Drift**
- **Single source of truth** for working configuration
- **Automated verification** prevents wrong deployments
- **Complete backups** preserve working state

### **Faster Recovery**
- **One-command recovery** from any backup
- **Dry-run mode** to preview changes
- **Automatic verification** after recovery

### **Better Debugging**
- **Complete system state** captured in backups
- **Service logs** included for analysis
- **Recovery instructions** in manifest

### **Reduced Frustration**
- **No more repeated debugging** of same issues
- **Clear documentation** of working configuration
- **Automated processes** reduce human error

## 📚 **Files Created**

1. **DEPLOYMENT_GUIDE.md** - Single source of truth
2. **backup-config.sh** - Configuration backup script
3. **recover.sh** - Recovery script
4. **Enhanced deploy-edge.sh** - Deployment with verification

## 🔧 **Maintenance**

### **Regular Backups**
```bash
# Create backup after any working deployment
./backup-config.sh
```

### **Before Major Changes**
```bash
# Always backup before changes
./backup-config.sh
```

### **After Fixes**
```bash
# Backup working state after fixes
./backup-config.sh
```

## 🚨 **Emergency Procedures**

### **If Everything Breaks**
1. **Stop all services**: `docker-compose -f docker-compose.asrock-edge.yml down`
2. **Recover from backup**: `./recover.sh latest --force`
3. **Verify**: `./deploy-edge.sh`

### **If Recovery Fails**
1. **Check emergency backup**: `ls -la backups/emergency-*`
2. **Manual recovery**: Follow instructions in `BACKUP_MANIFEST.txt`
3. **Contact support**: Provide backup directory and logs

## 📈 **Future Improvements**

1. **Automated backups** on successful deployments
2. **Health monitoring** with alerts
3. **Configuration validation** in CI/CD
4. **Rollback automation** for failed deployments

---

**This solution ensures you'll never have to debug the same WebRTC streaming issues repeatedly. The working configuration is preserved, verified, and easily recoverable.**

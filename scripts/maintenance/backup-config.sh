#!/bin/bash

# VAS Configuration Backup Script
# Creates a complete backup of the working configuration
# Author: VAS Development Team
# Version: 1.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
LATEST_LINK="backups/latest-working"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Check if system is in working state
check_working_state() {
    log "Checking if system is in working state..."
    
    # Check if Janus is using custom build
    JANUS_IMAGE=$(docker inspect janus-edge-001 2>/dev/null | jq -r '.[0].Config.Image' 2>/dev/null || echo "unknown")
    if [[ "$JANUS_IMAGE" != "vas_janus-edge" ]]; then
        warning "Janus is not using custom build ($JANUS_IMAGE)"
        warning "This backup may not represent a working configuration"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Backup cancelled"
            exit 1
        fi
    fi
    
    # Check if RTSP streams are active
    if ! docker logs janus-edge-001 2>&1 | grep -q "\[stream-1\]"; then
        warning "RTSP Stream 1 is not active"
    fi
    
    if ! docker logs janus-edge-001 2>&1 | grep -q "\[stream-2\]"; then
        warning "RTSP Stream 2 is not active"
    fi
    
    # Check backend API
    if ! curl -s http://localhost:8000/api/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        warning "Backend API is not healthy"
    fi
    
    success "System state checked"
}

# Create backup directory
create_backup_directory() {
    log "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    success "Backup directory created"
}

# Backup critical configuration files
backup_config_files() {
    log "Backing up critical configuration files..."
    
    # Janus configuration
    if [ -d "janus/config" ]; then
        cp -r janus/config/ "$BACKUP_DIR/"
        success "Janus configuration backed up"
    else
        warning "Janus config directory not found"
    fi
    
    # Docker Compose files
    if [ -f "docker-compose.asrock-edge.yml" ]; then
        cp docker-compose.asrock-edge.yml "$BACKUP_DIR/"
        success "Docker Compose configuration backed up"
    else
        warning "Docker Compose file not found"
    fi
    
    # Deployment script
    if [ -f "deploy-edge.sh" ]; then
        cp deploy-edge.sh "$BACKUP_DIR/"
        success "Deployment script backed up"
    else
        warning "Deployment script not found"
    fi
    
    # Nginx configuration
    if [ -f "nginx-edge.conf" ]; then
        cp nginx-edge.conf "$BACKUP_DIR/"
        success "Nginx configuration backed up"
    else
        warning "Nginx configuration not found"
    fi
    
    # Frontend distribution
    if [ -d "frontend-dist" ]; then
        cp -r frontend-dist/ "$BACKUP_DIR/"
        success "Frontend distribution backed up"
    else
        warning "Frontend distribution not found"
    fi
}

# Backup Docker state
backup_docker_state() {
    log "Backing up Docker state..."
    
    # Docker images
    docker images | grep -E "(janus|vas|edge)" > "$BACKUP_DIR/docker-images.txt" 2>/dev/null || true
    success "Docker images list backed up"
    
    # Docker containers
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" > "$BACKUP_DIR/docker-containers.txt" 2>/dev/null || true
    success "Docker containers list backed up"
    
    # Docker networks
    docker network ls > "$BACKUP_DIR/docker-networks.txt" 2>/dev/null || true
    success "Docker networks list backed up"
    
    # Docker volumes
    docker volume ls > "$BACKUP_DIR/docker-volumes.txt" 2>/dev/null || true
    success "Docker volumes list backed up"
}

# Backup system information
backup_system_info() {
    log "Backing up system information..."
    
    # System info
    uname -a > "$BACKUP_DIR/system-info.txt"
    echo "---" >> "$BACKUP_DIR/system-info.txt"
    cat /etc/os-release >> "$BACKUP_DIR/system-info.txt" 2>/dev/null || true
    
    # Docker version
    docker --version >> "$BACKUP_DIR/system-info.txt" 2>/dev/null || true
    docker-compose --version >> "$BACKUP_DIR/system-info.txt" 2>/dev/null || true
    
    # Network configuration
    ip addr show > "$BACKUP_DIR/network-config.txt" 2>/dev/null || true
    
    # Disk usage
    df -h > "$BACKUP_DIR/disk-usage.txt" 2>/dev/null || true
    
    # Memory info
    free -h > "$BACKUP_DIR/memory-info.txt" 2>/dev/null || true
    
    success "System information backed up"
}

# Backup service logs
backup_service_logs() {
    log "Backing up service logs..."
    
    # Create logs directory
    mkdir -p "$BACKUP_DIR/logs"
    
    # Backup Janus logs
    if docker ps | grep -q "janus-edge"; then
        docker logs janus-edge-001 > "$BACKUP_DIR/logs/janus-edge.log" 2>&1 || true
        success "Janus logs backed up"
    fi
    
    # Backup backend logs
    if docker ps | grep -q "vas-backend-edge"; then
        docker logs vas-backend-edge-001 > "$BACKUP_DIR/logs/vas-backend-edge.log" 2>&1 || true
        success "Backend logs backed up"
    fi
    
    # Backup database logs
    if docker ps | grep -q "edge-db"; then
        docker logs edge-db-001 > "$BACKUP_DIR/logs/edge-db.log" 2>&1 || true
        success "Database logs backed up"
    fi
    
    # Backup Redis logs
    if docker ps | grep -q "edge-redis"; then
        docker logs edge-redis-001 > "$BACKUP_DIR/logs/edge-redis.log" 2>&1 || true
        success "Redis logs backed up"
    fi
    
    # Backup Nginx logs
    if docker ps | grep -q "nginx-edge"; then
        docker logs nginx-edge-001 > "$BACKUP_DIR/logs/nginx-edge.log" 2>&1 || true
        success "Nginx logs backed up"
    fi
}

# Create backup manifest
create_backup_manifest() {
    log "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
VAS Configuration Backup Manifest
=================================

Backup Date: $(date)
Backup Directory: $BACKUP_DIR
System: $(uname -a)

Critical Files Backed Up:
- janus/config/ (Janus configuration)
- docker-compose.asrock-edge.yml (Docker Compose configuration)
- deploy-edge.sh (Deployment script)
- nginx-edge.conf (Nginx configuration)
- frontend-dist/ (Frontend distribution)

Docker State:
- Images: docker-images.txt
- Containers: docker-containers.txt
- Networks: docker-networks.txt
- Volumes: docker-volumes.txt

System Information:
- system-info.txt (OS, Docker versions)
- network-config.txt (Network configuration)
- disk-usage.txt (Disk usage)
- memory-info.txt (Memory information)

Service Logs:
- logs/janus-edge.log
- logs/vas-backend-edge.log
- logs/edge-db.log
- logs/edge-redis.log
- logs/nginx-edge.log

Recovery Instructions:
1. Stop all services: docker-compose -f docker-compose.asrock-edge.yml down
2. Restore configuration: cp -r $BACKUP_DIR/* ./
3. Rebuild custom Janus: docker-compose -f docker-compose.asrock-edge.yml build janus-edge
4. Start services: docker-compose -f docker-compose.asrock-edge.yml up -d
5. Verify: ./deploy-edge.sh

Notes:
- This backup represents a working configuration
- Janus image: vas_janus-edge (custom build)
- RTSP authentication: digest method
- Database IP: 172.21.0.3 (for host networking)
EOF
    
    success "Backup manifest created"
}

# Create latest link
create_latest_link() {
    log "Creating latest working link..."
    
    # Remove existing latest link
    rm -f "$LATEST_LINK"
    
    # Create new latest link
    ln -s "$(basename "$BACKUP_DIR")" "$LATEST_LINK"
    
    success "Latest working link created: $LATEST_LINK -> $BACKUP_DIR"
}

# Display backup summary
display_backup_summary() {
    success "📦 Configuration Backup Complete!"
    echo
    echo "📊 Backup Summary:"
    echo "  • Backup Directory: $BACKUP_DIR"
    echo "  • Latest Link: $LATEST_LINK"
    echo "  • Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo
    echo "📁 Backup Contents:"
    echo "  • Configuration files"
    echo "  • Docker state information"
    echo "  • System information"
    echo "  • Service logs"
    echo "  • Recovery instructions"
    echo
    echo "🔄 Recovery Commands:"
    echo "  • Quick recovery: ./recover.sh $BACKUP_DIR"
    echo "  • Latest recovery: ./recover.sh $LATEST_LINK"
    echo "  • Manual recovery: See BACKUP_MANIFEST.txt"
    echo
}

# Main backup function
main() {
    echo "📦 VAS Configuration Backup"
    echo "=========================="
    echo
    
    # Check if running as root or with sudo
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root. This is not recommended for Docker operations."
    fi
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not available"
        exit 1
    fi
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        warning "jq is not installed. Some verification steps may fail."
    fi
    
    # Run backup steps
    check_working_state
    create_backup_directory
    backup_config_files
    backup_docker_state
    backup_system_info
    backup_service_logs
    create_backup_manifest
    create_latest_link
    display_backup_summary
}

# Run main function with all arguments
main "$@"

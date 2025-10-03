#!/bin/bash

# VAS Configuration Recovery Script
# Recovers from a working configuration backup
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
COMPOSE_FILE="docker-compose.asrock-edge.yml"

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

# Show usage information
show_usage() {
    echo "Usage: $0 <backup-directory> [OPTIONS]"
    echo
    echo "Arguments:"
    echo "  backup-directory    Path to backup directory or 'latest' for latest backup"
    echo
    echo "Options:"
    echo "  --force            Force recovery without confirmation"
    echo "  --dry-run          Show what would be recovered without making changes"
    echo "  --help             Show this help message"
    echo
    echo "Examples:"
    echo "  $0 backups/20250917_143022"
    echo "  $0 latest"
    echo "  $0 backups/20250917_143022 --dry-run"
    echo
    echo "Available backups:"
    if [ -d "backups" ]; then
        ls -la backups/ 2>/dev/null | grep "^d" | awk '{print "  " $9}' | grep -v "^\.$\|^\.\.$" || echo "  No backups found"
    else
        echo "  No backups directory found"
    fi
}

# Validate backup directory
validate_backup_directory() {
    local backup_dir="$1"
    
    # Handle 'latest' shortcut
    if [[ "$backup_dir" == "latest" ]]; then
        if [ -L "backups/latest-working" ]; then
            backup_dir="backups/$(readlink backups/latest-working)"
        else
            error "No latest backup link found"
            exit 1
        fi
    fi
    
    # Check if backup directory exists
    if [ ! -d "$backup_dir" ]; then
        error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    # Check if backup manifest exists
    if [ ! -f "$backup_dir/BACKUP_MANIFEST.txt" ]; then
        error "Invalid backup directory: No BACKUP_MANIFEST.txt found"
        exit 1
    fi
    
    # Check if critical files exist
    local missing_files=()
    [ ! -d "$backup_dir/janus" ] && [ ! -d "$backup_dir/config" ] && missing_files+=("janus/config or config")
    [ ! -f "$backup_dir/docker-compose.asrock-edge.yml" ] && missing_files+=("docker-compose.asrock-edge.yml")
    [ ! -f "$backup_dir/deploy-edge.sh" ] && missing_files+=("deploy-edge.sh")
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Invalid backup directory: Missing critical files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    success "Backup directory validated: $backup_dir"
}

# Show backup information
show_backup_info() {
    local backup_dir="$1"
    
    log "Backup Information:"
    echo "  Directory: $backup_dir"
    echo "  Date: $(grep "Backup Date:" "$backup_dir/BACKUP_MANIFEST.txt" | cut -d: -f2- | xargs)"
    echo "  Size: $(du -sh "$backup_dir" | cut -f1)"
    echo
    echo "Contents:"
    grep -A 20 "Critical Files Backed Up:" "$backup_dir/BACKUP_MANIFEST.txt" | head -10
    echo
}

# Confirm recovery
confirm_recovery() {
    local backup_dir="$1"
    
    if [[ "${FORCE:-false}" == "true" ]]; then
        return 0
    fi
    
    warning "This will overwrite your current configuration!"
    echo
    echo "Current services will be stopped and configuration restored from:"
    echo "  $backup_dir"
    echo
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Recovery cancelled"
        exit 1
    fi
}

# Stop current services
stop_current_services() {
    log "Stopping current services..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" down || warning "Some services may not have stopped cleanly"
        success "Current services stopped"
    else
        warning "No docker-compose file found to stop services"
    fi
}

# Backup current state
backup_current_state() {
    log "Creating emergency backup of current state..."
    
    local emergency_backup="backups/emergency-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$emergency_backup"
    
    # Backup current configuration
    [ -d "janus/config" ] && cp -r janus/config/ "$emergency_backup/" 2>/dev/null || true
    [ -f "$COMPOSE_FILE" ] && cp "$COMPOSE_FILE" "$emergency_backup/" 2>/dev/null || true
    [ -f "deploy-edge.sh" ] && cp deploy-edge.sh "$emergency_backup/" 2>/dev/null || true
    [ -f "nginx-edge.conf" ] && cp nginx-edge.conf "$emergency_backup/" 2>/dev/null || true
    
    success "Emergency backup created: $emergency_backup"
}

# Restore configuration files
restore_config_files() {
    local backup_dir="$1"
    
    log "Restoring configuration files..."
    
    # Restore Janus configuration
    if [ -d "$backup_dir/janus" ]; then
        rm -rf janus/config
        cp -r "$backup_dir/janus/config" janus/
        success "Janus configuration restored"
    elif [ -d "$backup_dir/config" ]; then
        rm -rf janus/config
        cp -r "$backup_dir/config" janus/
        success "Janus configuration restored"
    fi
    
    # Restore Docker Compose file
    if [ -f "$backup_dir/docker-compose.asrock-edge.yml" ]; then
        cp "$backup_dir/docker-compose.asrock-edge.yml" .
        success "Docker Compose configuration restored"
    fi
    
    # Restore deployment script
    if [ -f "$backup_dir/deploy-edge.sh" ]; then
        cp "$backup_dir/deploy-edge.sh" .
        chmod +x deploy-edge.sh
        success "Deployment script restored"
    fi
    
    # Restore Nginx configuration
    if [ -f "$backup_dir/nginx-edge.conf" ]; then
        cp "$backup_dir/nginx-edge.conf" .
        success "Nginx configuration restored"
    fi
    
    # Restore frontend distribution
    if [ -d "$backup_dir/frontend-dist" ]; then
        rm -rf frontend-dist
        cp -r "$backup_dir/frontend-dist" .
        success "Frontend distribution restored"
    fi
}

# Rebuild custom Janus image
rebuild_janus_image() {
    log "Rebuilding custom Janus image..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" build janus-edge
        success "Custom Janus image rebuilt"
    else
        error "Docker Compose file not found for rebuilding Janus"
        return 1
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" up -d
        success "Services started"
    else
        error "Docker Compose file not found for starting services"
        return 1
    fi
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to become ready..."
    
    local services=("edge-db" "edge-redis" "janus-edge" "vas-backend-edge" "nginx-edge")
    local max_wait=300
    local wait_time=0
    
    for service in "${services[@]}"; do
        log "Waiting for $service..."
        
        while [ $wait_time -lt $max_wait ]; do
            if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy\|Up"; then
                success "$service is ready"
                break
            fi
            
            sleep 10
            wait_time=$((wait_time + 10))
            
            if [ $wait_time -ge $max_wait ]; then
                error "$service failed to start within $max_wait seconds"
                return 1
            fi
        done
    done
}

# Verify recovery
verify_recovery() {
    log "Verifying recovery..."
    
    # Check Janus image
    local janus_image=$(docker inspect janus-edge-001 2>/dev/null | jq -r '.[0].Config.Image' 2>/dev/null || echo "unknown")
    if [[ "$janus_image" == "vas_janus-edge" ]]; then
        success "Janus: Custom build (vas_janus-edge)"
    else
        error "Janus: Wrong image ($janus_image) - should be vas_janus-edge"
        return 1
    fi
    
    # Check RTSP streams
    sleep 30  # Wait for Janus to fully initialize
    
    if docker logs janus-edge-001 2>&1 | grep -q "\[stream-1\]"; then
        success "RTSP Stream 1: Active"
    else
        warning "RTSP Stream 1: Not active yet"
    fi
    
    if docker logs janus-edge-001 2>&1 | grep -q "\[stream-2\]"; then
        success "RTSP Stream 2: Active"
    else
        warning "RTSP Stream 2: Not active yet"
    fi
    
    # Check backend API
    if curl -s http://localhost:8000/api/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        success "Backend API: Healthy"
    else
        warning "Backend API: Not healthy yet"
    fi
    
    success "Recovery verification completed"
}

# Display recovery summary
display_recovery_summary() {
    success "🔄 Configuration Recovery Complete!"
    echo
    echo "📊 Recovery Summary:"
    echo "  • Configuration restored from backup"
    echo "  • Custom Janus image rebuilt"
    echo "  • Services restarted"
    echo
    echo "🔍 Next Steps:"
    echo "  • Check service logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  • Verify video feeds: Open http://localhost in browser"
    echo "  • Run full verification: ./deploy-edge.sh"
    echo
    echo "📈 Service URLs:"
    echo "  • Frontend: http://localhost"
    echo "  • Backend API: http://localhost:8000"
    echo "  • Janus API: http://localhost:8088"
    echo
}

# Dry run mode
dry_run() {
    local backup_dir="$1"
    
    log "DRY RUN MODE - No changes will be made"
    echo
    echo "Would restore from: $backup_dir"
    echo
    echo "Files that would be restored:"
    ([ -d "$backup_dir/janus" ] || [ -d "$backup_dir/config" ]) && echo "  ✓ janus/config/"
    [ -f "$backup_dir/docker-compose.asrock-edge.yml" ] && echo "  ✓ docker-compose.asrock-edge.yml"
    [ -f "$backup_dir/deploy-edge.sh" ] && echo "  ✓ deploy-edge.sh"
    [ -f "$backup_dir/nginx-edge.conf" ] && echo "  ✓ nginx-edge.conf"
    [ -d "$backup_dir/frontend-dist" ] && echo "  ✓ frontend-dist/"
    echo
    echo "Actions that would be performed:"
    echo "  1. Stop current services"
    echo "  2. Create emergency backup"
    echo "  3. Restore configuration files"
    echo "  4. Rebuild custom Janus image"
    echo "  5. Start services"
    echo "  6. Verify recovery"
    echo
    success "Dry run completed - no changes made"
}

# Main recovery function
main() {
    echo "🔄 VAS Configuration Recovery"
    echo "============================="
    echo
    
    # Parse command line arguments
    local backup_dir=""
    local dry_run_mode=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                export FORCE=true
                shift
                ;;
            --dry-run)
                dry_run_mode=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$backup_dir" ]; then
                    backup_dir="$1"
                else
                    error "Multiple backup directories specified"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Check if backup directory was provided
    if [ -z "$backup_dir" ]; then
        error "No backup directory specified"
        show_usage
        exit 1
    fi
    
    # Validate backup directory
    validate_backup_directory "$backup_dir"
    
    # Show backup information
    show_backup_info "$backup_dir"
    
    # Handle dry run mode
    if [[ "$dry_run_mode" == "true" ]]; then
        dry_run "$backup_dir"
        exit 0
    fi
    
    # Confirm recovery
    confirm_recovery "$backup_dir"
    
    # Run recovery steps
    stop_current_services
    backup_current_state
    restore_config_files "$backup_dir"
    rebuild_janus_image
    start_services
    wait_for_services
    verify_recovery
    display_recovery_summary
}

# Run main function with all arguments
main "$@"

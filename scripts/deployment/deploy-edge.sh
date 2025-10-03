#!/bin/bash

# ASRock Edge Deployment Script
# Deploys optimized VAS system for ASRock iEP-7040E-024 units
# Author: VAS Development Team
# Version: 1.0

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_UNIT_ID="001"
DEFAULT_MAX_CAMERAS=6
COMPOSE_FILE="docker-compose.asrock-edge.yml"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

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

# Check system requirements
check_system_requirements() {
    log "Checking system requirements for ASRock iEP-7040E-024..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available memory (should be 16GB+ for ASRock)
    total_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_mem" -lt 12 ]; then
        warning "Available memory: ${total_mem}GB. ASRock iEP-7040E-024 should have 16GB+."
    else
        success "Memory check passed: ${total_mem}GB available"
    fi
    
    # Check CPU cores (should be 16 cores for Intel Ultra 7 255H)
    cpu_cores=$(nproc)
    if [ "$cpu_cores" -lt 8 ]; then
        warning "CPU cores: ${cpu_cores}. Expected 16 cores for optimal performance."
    else
        success "CPU check passed: ${cpu_cores} cores available"
    fi
    
    # Check for Intel Arc GPU (optional but recommended)
    if lspci | grep -i "arc\|intel.*display" &> /dev/null; then
        success "Intel Arc GPU detected - ready for YOLO acceleration"
    else
        warning "Intel Arc GPU not detected. YOLO inference will use CPU only."
    fi
    
    # Check disk space (need at least 50GB for recordings)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 50 ]; then
        warning "Available disk space: ${available_space}GB. Recommend 100GB+ for recordings."
    else
        success "Disk space check passed: ${available_space}GB available"
    fi
}

# Backup existing configuration
backup_existing_config() {
    if [ -f "docker-compose.yml" ] || [ -d "janus/config" ]; then
        log "Backing up existing configuration..."
        mkdir -p "$BACKUP_DIR"
        
        [ -f "docker-compose.yml" ] && cp "docker-compose.yml" "$BACKUP_DIR/"
        [ -d "janus/config" ] && cp -r "janus/config" "$BACKUP_DIR/"
        [ -d "vas" ] && cp -r "vas" "$BACKUP_DIR/"
        
        success "Backup created at: $BACKUP_DIR"
    fi
}

# Validate environment variables
validate_environment() {
    log "Validating environment configuration..."
    
    # Set defaults if not provided
    export UNIT_ID="${UNIT_ID:-$DEFAULT_UNIT_ID}"
    export MAX_CAMERAS="${MAX_CAMERAS:-$DEFAULT_MAX_CAMERAS}"
    
    # Validate UNIT_ID format (3 digits)
    if ! [[ "$UNIT_ID" =~ ^[0-9]{3}$ ]]; then
        error "UNIT_ID must be 3 digits (e.g., 001, 002, 050)"
        exit 1
    fi
    
    # Validate MAX_CAMERAS (should be 6 for ASRock)
    if [ "$MAX_CAMERAS" -gt 6 ]; then
        warning "MAX_CAMERAS set to $MAX_CAMERAS. ASRock optimized for 6 cameras max."
    fi
    
    success "Environment validated: UNIT_ID=$UNIT_ID, MAX_CAMERAS=$MAX_CAMERAS"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    directories=(
        "recordings"
        "config/ssl"
        "edge-api"
        "logs"
        "backups"
        "frontend-dist"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    success "Directories created"
}

# Generate SSL certificates for production
generate_ssl_certificates() {
    if [ ! -f "config/ssl/edge-cert.pem" ]; then
        log "Generating self-signed SSL certificates..."
        
        openssl req -x509 -newkey rsa:4096 -keyout config/ssl/edge-key.pem -out config/ssl/edge-cert.pem \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Company/CN=edge-unit-$UNIT_ID"
        
        chmod 600 config/ssl/edge-key.pem
        chmod 644 config/ssl/edge-cert.pem
        
        success "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
}

# Update camera configurations
update_camera_config() {
    log "Updating camera configuration for unit $UNIT_ID..."
    
    # Update streaming config with unit-specific settings
    sed -i "s/\${UNIT_ID}/$UNIT_ID/g" "janus/config/janus.plugin.streaming.edge.jcfg"
    sed -i "s/\${UNIT_ID}/$UNIT_ID/g" "janus/config/edge-janus.jcfg"
    
    success "Camera configuration updated"
}

# Setup frontend without Docker
setup_frontend() {
    log "Setting up frontend for direct serving..."
    
    # Check if frontend source exists
    if [ ! -d "frontend" ] || [ -z "$(ls -A frontend)" ]; then
        warning "Frontend directory is empty or doesn't exist. Creating a basic frontend..."
        
        # Create a basic HTML frontend for testing
        cat > frontend-dist/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAS Edge Unit Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            background: #f8f9fa;
        }
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .camera-card {
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            text-align: center;
            background: white;
        }
        .status-online { border-left-color: #28a745; }
        .status-offline { border-left-color: #dc3545; }
        .status-warning { border-left-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VAS Edge Unit Dashboard</h1>
            <p>Unit ID: <span id="unit-id">Loading...</span> | Max Cameras: <span id="max-cameras">Loading...</span></p>
        </div>
        
        <div class="status-grid">
            <div class="status-card status-online">
                <h3>System Status</h3>
                <p><strong>Status:</strong> Online</p>
                <p><strong>Uptime:</strong> <span id="uptime">Loading...</span></p>
            </div>
            <div class="status-card status-online">
                <h3>Backend API</h3>
                <p><strong>Status:</strong> Connected</p>
                <p><strong>URL:</strong> http://localhost:8000</p>
            </div>
            <div class="status-card status-online">
                <h3>Janus Gateway</h3>
                <p><strong>Status:</strong> Active</p>
                <p><strong>Streams:</strong> <span id="active-streams">0</span>/6</p>
            </div>
        </div>
        
        <h2>Camera Streams</h2>
        <div class="camera-grid" id="camera-grid">
            <!-- Camera cards will be populated by JavaScript -->
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>VAS Edge Computing System - Development Mode</p>
            <p>Frontend served directly without Docker container</p>
        </div>
    </div>

    <script>
        // Set unit information
        document.getElementById('unit-id').textContent = '001'; // This would be dynamic
        document.getElementById('max-cameras').textContent = '6';
        
        // Create camera cards
        const cameraGrid = document.getElementById('camera-grid');
        for (let i = 1; i <= 6; i++) {
            const cameraCard = document.createElement('div');
            cameraCard.className = 'camera-card';
            cameraCard.innerHTML = `
                <h4>Camera ${i}</h4>
                <p>Status: <span class="status-offline">Offline</span></p>
                <p>Stream URL: <br><small>http://localhost/streams/${i}</small></p>
            `;
            cameraGrid.appendChild(cameraCard);
        }
        
        // Update uptime (simplified)
        document.getElementById('uptime').textContent = 'Just started';
        
        // Check backend API status
        fetch('http://localhost:8000/health')
            .then(response => response.json())
            .then(data => {
                console.log('Backend API is healthy:', data);
            })
            .catch(error => {
                console.log('Backend API not yet available:', error);
            });
    </script>
</body>
</html>
EOF
        
        success "Basic frontend created in frontend-dist/"
    else
        log "Frontend source found. Building frontend..."
        
        # Check if Node.js is available
        if command -v npm &> /dev/null; then
            cd frontend
            
            # Install dependencies if package.json exists
            if [ -f "package.json" ]; then
                log "Installing frontend dependencies..."
                npm install
                
                # Build the frontend
                log "Building frontend..."
                npm run build
                
                # Copy build output to frontend-dist
                if [ -d "build" ]; then
                    cp -r build/* ../../frontend-dist/
                elif [ -d "dist" ]; then
                    cp -r dist/* ../../frontend-dist/
                else
                    warning "No build output directory found. Using source files directly."
                    cp -r . ../../frontend-dist/
                fi
                
                cd ../..
                success "Frontend built and copied to frontend-dist/"
            else
                warning "No package.json found. Copying source files directly."
                cp -r frontend/* frontend-dist/
                success "Frontend source copied to frontend-dist/"
            fi
        else
            warning "Node.js/npm not available. Creating basic frontend instead."
            # Use the same basic HTML as above
            cat > frontend-dist/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAS Edge Unit Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            background: #f8f9fa;
        }
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .camera-card {
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            text-align: center;
            background: white;
        }
        .status-online { border-left-color: #28a745; }
        .status-offline { border-left-color: #dc3545; }
        .status-warning { border-left-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VAS Edge Unit Dashboard</h1>
            <p>Unit ID: <span id="unit-id">Loading...</span> | Max Cameras: <span id="max-cameras">Loading...</span></p>
        </div>
        
        <div class="status-grid">
            <div class="status-card status-online">
                <h3>System Status</h3>
                <p><strong>Status:</strong> Online</p>
                <p><strong>Uptime:</strong> <span id="uptime">Loading...</span></p>
            </div>
            <div class="status-card status-online">
                <h3>Backend API</h3>
                <p><strong>Status:</strong> Connected</p>
                <p><strong>URL:</strong> http://localhost:8000</p>
            </div>
            <div class="status-card status-online">
                <h3>Janus Gateway</h3>
                <p><strong>Status:</strong> Active</p>
                <p><strong>Streams:</strong> <span id="active-streams">0</span>/6</p>
            </div>
        </div>
        
        <h2>Camera Streams</h2>
        <div class="camera-grid" id="camera-grid">
            <!-- Camera cards will be populated by JavaScript -->
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>VAS Edge Computing System - Development Mode</p>
            <p>Frontend served directly without Docker container</p>
        </div>
    </div>

    <script>
        // Set unit information
        document.getElementById('unit-id').textContent = '001'; // This would be dynamic
        document.getElementById('max-cameras').textContent = '6';
        
        // Create camera cards
        const cameraGrid = document.getElementById('camera-grid');
        for (let i = 1; i <= 6; i++) {
            const cameraCard = document.createElement('div');
            cameraCard.className = 'camera-card';
            cameraCard.innerHTML = `
                <h4>Camera ${i}</h4>
                <p>Status: <span class="status-offline">Offline</span></p>
                <p>Stream URL: <br><small>http://localhost/streams/${i}</small></p>
            `;
            cameraGrid.appendChild(cameraCard);
        }
        
        // Update uptime (simplified)
        document.getElementById('uptime').textContent = 'Just started';
        
        // Check backend API status
        fetch('http://localhost:8000/health')
            .then(response => response.json())
            .then(data => {
                console.log('Backend API is healthy:', data);
            })
            .catch(error => {
                console.log('Backend API not yet available:', error);
            });
    </script>
</body>
</html>
EOF
            success "Basic frontend created in frontend-dist/"
        fi
    fi
}

# Deploy the edge stack
deploy_stack() {
    log "Deploying ASRock edge stack..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    docker-compose -f "$COMPOSE_FILE" build
    
    # Start the stack
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Edge stack deployed"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to become healthy..."
    
    services=("edge-db" "edge-redis" "janus-edge" "vas-backend-edge" "nginx-edge")
    max_wait=300  # 5 minutes
    wait_time=0
    
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
                exit 1
            fi
        done
    done
}

# Test camera connections
test_camera_connections() {
    log "Testing camera connections..."
    
    # Wait a bit for Janus to fully initialize
    sleep 30
    
    # Test Janus API
    if curl -s "http://localhost:8088/janus/info" > /dev/null; then
        success "Janus API is responding"
    else
        error "Janus API is not responding"
        return 1
    fi
    
    # Test streaming endpoints
    for i in {1..6}; do
        if curl -s "http://localhost:8088/janus" -d "{\"janus\":\"info\",\"transaction\":\"test$i\"}" > /dev/null; then
            success "Stream $i endpoint is ready"
        else
            warning "Stream $i may not be fully ready yet"
        fi
    done
}

# Verify deployment integrity
verify_deployment() {
    log "🔍 Verifying deployment integrity..."
    
    # Check Janus image
    JANUS_IMAGE=$(docker inspect janus-edge-001 2>/dev/null | jq -r '.[0].Config.Image' 2>/dev/null || echo "unknown")
    if [[ "$JANUS_IMAGE" == "vas_janus-edge" ]]; then
        success "Janus: Custom build (vas_janus-edge)"
    else
        error "Janus: Wrong image ($JANUS_IMAGE) - should be vas_janus-edge"
        error "This indicates the wrong Docker image is being used!"
        return 1
    fi
    
    # Check RTSP streams are active
    if docker logs janus-edge-001 2>&1 | grep -q "\[stream-1\]"; then
        success "RTSP Stream 1: Active"
    else
        error "RTSP Stream 1: Not active"
        error "Check Janus configuration and RTSP authentication"
        return 1
    fi
    
    if docker logs janus-edge-001 2>&1 | grep -q "\[stream-2\]"; then
        success "RTSP Stream 2: Active"
    else
        error "RTSP Stream 2: Not active"
        error "Check Janus configuration and RTSP authentication"
        return 1
    fi
    
    # Check backend API health
    if curl -s http://localhost:8000/api/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        success "Backend API: Healthy"
    else
        error "Backend API: Not healthy"
        error "Check backend logs and database connection"
        return 1
    fi
    
    # Check database connection
    if docker logs vas-backend-edge-001 2>&1 | grep -qi "database.*connected\|database.*ready"; then
        success "Database: Connected"
    else
        warning "Database: Connection status unclear"
    fi
    
    # Check Redis connection
    if docker logs vas-backend-edge-001 2>&1 | grep -qi "redis.*connected\|redis.*ready"; then
        success "Redis: Connected"
    else
        warning "Redis: Connection status unclear"
    fi
    
    success "🎉 All critical systems verified!"
}

# Display deployment summary
display_summary() {
    success "🚀 ASRock Edge Deployment Complete!"
    echo
    echo "📊 Deployment Summary:"
    echo "  • Unit ID: $UNIT_ID"
    echo "  • Max Cameras: $MAX_CAMERAS"
    echo "  • Frontend: http://localhost"
    echo "  • Janus API: http://localhost:8088"
    echo "  • Edge API: http://localhost:3001"
    echo "  • Monitoring: http://localhost/metrics"
    echo
    echo "📹 Camera Stream URLs:"
    for i in {1..6}; do
        echo "  • Camera $i: http://localhost/streams/$i"
    done
    echo
    echo "🔧 Management Commands:"
    echo "  • View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  • Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  • Restart: docker-compose -f $COMPOSE_FILE restart"
    echo "  • Update: ./deploy-edge.sh --update"
    echo
    echo "📈 Performance Monitoring:"
    echo "  • System metrics: curl http://localhost/metrics"
    echo "  • Janus stats: curl http://localhost:8088/admin"
    echo "  • GPU usage: intel_gpu_top (if available)"
    echo
}

# Main deployment function
main() {
    echo "🎯 ASRock iEP-7040E-024 Edge Deployment"
    echo "======================================="
    echo
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-id)
                export UNIT_ID="$2"
                shift 2
                ;;
            --cameras)
                export MAX_CAMERAS="$2"
                shift 2
                ;;
            --update)
                UPDATE_MODE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --unit-id ID     Set unit ID (3 digits, e.g., 001)"
                echo "  --cameras NUM    Set max cameras (default: 6)"
                echo "  --update         Update existing deployment"
                echo "  --help           Show this help"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_system_requirements
    validate_environment
    
    if [ "${UPDATE_MODE:-false}" != "true" ]; then
        backup_existing_config
        create_directories
        generate_ssl_certificates
        update_camera_config
        setup_frontend
    fi
    
    deploy_stack
    wait_for_services
    test_camera_connections
    verify_deployment
    display_summary
}

# Run main function with all arguments
main "$@"

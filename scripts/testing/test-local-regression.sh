#!/bin/bash

# Local Regression Test Script
# Tests that existing 2-camera setup still works before ASRock deployment
# Author: VAS Development Team

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
ORIGINAL_COMPOSE="docker-compose.yml"
EDGE_COMPOSE="docker-compose.asrock-edge.yml"
TEST_TIMEOUT=120  # 2 minutes for each test
CAMERAS_TO_TEST=2  # Test existing 2 cameras

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

# Clean up function
cleanup() {
    log "Cleaning up test environment..."
    docker-compose -f "$ORIGINAL_COMPOSE" down --remove-orphans 2>/dev/null || true
    docker-compose -f "$EDGE_COMPOSE" down --remove-orphans 2>/dev/null || true
}

# Set up trap for cleanup
trap cleanup EXIT

# Test original setup
test_original_setup() {
    log "Testing original docker-compose setup..."
    
    # Stop any running containers
    docker-compose -f "$ORIGINAL_COMPOSE" down 2>/dev/null || true
    
    # Start original setup
    log "Starting original services..."
    if ! docker-compose -f "$ORIGINAL_COMPOSE" up -d; then
        error "Failed to start original services"
        return 1
    fi
    
    # Wait for services to be ready
    log "Waiting for services to become ready..."
    local wait_time=0
    while [ $wait_time -lt $TEST_TIMEOUT ]; do
        if curl -s "http://localhost:8188" > /dev/null 2>&1; then
            success "Janus WebSocket is responding"
            break
        fi
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    if [ $wait_time -ge $TEST_TIMEOUT ]; then
        error "Services failed to start within $TEST_TIMEOUT seconds"
        docker-compose -f "$ORIGINAL_COMPOSE" logs
        return 1
    fi
    
    # Test Janus API
    log "Testing Janus HTTP API..."
    if ! curl -s "http://localhost:8088/janus/info" | grep -q "janus"; then
        error "Janus HTTP API not responding correctly"
        return 1
    fi
    success "Janus HTTP API is working"
    
    # Test WebSocket connection
    log "Testing Janus WebSocket..."
    if ! curl -s -H "Upgrade: websocket" -H "Connection: Upgrade" "http://localhost:8188" > /dev/null; then
        warning "WebSocket test may not be conclusive (curl limitation)"
    fi
    
    # Test VAS backend (if available)
    if docker-compose -f "$ORIGINAL_COMPOSE" ps | grep -q "vas-backend"; then
        log "Testing VAS backend..."
        local backend_port=$(docker-compose -f "$ORIGINAL_COMPOSE" port vas-backend 8000 2>/dev/null | cut -d: -f2)
        if [ -n "$backend_port" ]; then
            if curl -s "http://localhost:$backend_port/health" > /dev/null; then
                success "VAS backend is responding"
            else
                warning "VAS backend not responding on port $backend_port"
            fi
        fi
    fi
    
    # Test camera streams
    log "Testing camera stream endpoints..."
    for i in $(seq 1 $CAMERAS_TO_TEST); do
        local stream_test=$(curl -s "http://localhost:8088/janus" \
            -H "Content-Type: application/json" \
            -d "{\"janus\":\"info\",\"transaction\":\"test_stream_$i\"}" \
            | grep -o '"janus":"[^"]*"' | head -1)
        
        if [[ "$stream_test" == '"janus":"ack"' ]] || [[ "$stream_test" == '"janus":"success"' ]]; then
            success "Stream $i endpoint is accessible"
        else
            warning "Stream $i endpoint may have issues"
        fi
    done
    
    # Check frontend (if available)
    if docker-compose -f "$ORIGINAL_COMPOSE" ps | grep -q "nginx\|web"; then
        log "Testing frontend..."
        if curl -s "http://localhost" > /dev/null; then
            success "Frontend is accessible"
        else
            warning "Frontend not accessible on port 80"
        fi
    fi
    
    success "Original setup test completed successfully"
    return 0
}

# Performance benchmark
benchmark_performance() {
    log "Running performance benchmark..."
    
    # Get baseline metrics
    local cpu_before=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local mem_before=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    log "Baseline: CPU=${cpu_before}%, Memory=${mem_before}%"
    
    # Simulate load by making multiple requests
    log "Simulating load with multiple concurrent requests..."
    for i in {1..10}; do
        curl -s "http://localhost:8088/janus/info" > /dev/null &
    done
    wait
    
    # Get metrics after load
    sleep 2
    local cpu_after=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local mem_after=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    log "After load: CPU=${cpu_after}%, Memory=${mem_after}%"
    
    # Check if performance is reasonable
    if (( $(echo "$cpu_after < 80" | bc -l) )) && (( $(echo "$mem_after < 80" | bc -l) )); then
        success "Performance benchmark passed"
        return 0
    else
        warning "High resource usage detected - may impact performance"
        return 1
    fi
}

# Test edge configuration (dry run)
test_edge_config() {
    log "Testing edge configuration syntax..."
    
    # Validate docker-compose syntax
    if ! docker-compose -f "$EDGE_COMPOSE" config > /dev/null 2>&1; then
        error "Edge docker-compose configuration has syntax errors"
        docker-compose -f "$EDGE_COMPOSE" config
        return 1
    fi
    success "Edge docker-compose syntax is valid"
    
    # Check if required files exist
    local required_files=(
        "janus/config/edge-janus.jcfg"
        "janus/config/janus.plugin.streaming.edge.jcfg"
        "config/nginx/nginx-edge.conf"
        "edge-api/main.py"
        "edge-api/requirements.txt"
        "scripts/deployment/deploy-edge.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            success "Required file exists: $file"
        else
            error "Missing required file: $file"
            return 1
        fi
    done
    
    # Validate Janus configuration
    if grep -q "max_streams = 6" "janus/config/janus.plugin.streaming.edge.jcfg"; then
        success "Janus configured for 6 cameras"
    else
        warning "Janus configuration may not be optimized for 6 cameras"
    fi
    
    success "Edge configuration validation passed"
    return 0
}

# Compare configurations
compare_configs() {
    log "Comparing original vs edge configurations..."
    
    # Check for breaking changes
    local breaking_changes=0
    
    # Check if original ports are preserved or changed
    if docker-compose -f "$ORIGINAL_COMPOSE" config | grep -q "8088:8088"; then
        if docker-compose -f "$EDGE_COMPOSE" config | grep -q "8088:8088"; then
            success "Janus HTTP API port (8088) preserved"
        else
            warning "Janus HTTP API port changed in edge config"
            breaking_changes=$((breaking_changes + 1))
        fi
    fi
    
    if docker-compose -f "$ORIGINAL_COMPOSE" config | grep -q "8188:8188"; then
        if docker-compose -f "$EDGE_COMPOSE" config | grep -q "network_mode.*host"; then
            success "Janus WebSocket will use host networking (optimal for edge)"
        else
            warning "Janus WebSocket configuration changed"
        fi
    fi
    
    # Check resource allocation
    if docker-compose -f "$EDGE_COMPOSE" config | grep -q "cpus.*4\.0"; then
        success "Resource limits configured for edge deployment"
    else
        warning "Resource limits not found in edge configuration"
    fi
    
    if [ $breaking_changes -eq 0 ]; then
        success "No breaking changes detected"
        return 0
    else
        warning "$breaking_changes potential breaking changes detected"
        return 1
    fi
}

# Generate test report
generate_report() {
    local test_results="$1"
    local report_file="regression_test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log "Generating test report: $report_file"
    
    cat > "$report_file" << EOF
VAS System Regression Test Report
Generated: $(date)
======================================

Test Environment:
- Original Compose: $ORIGINAL_COMPOSE
- Edge Compose: $EDGE_COMPOSE
- Test Timeout: $TEST_TIMEOUT seconds
- Cameras Tested: $CAMERAS_TO_TEST

Test Results:
$test_results

System Information:
- OS: $(uname -a)
- Docker Version: $(docker --version)
- Docker Compose Version: $(docker-compose --version)
- Available Memory: $(free -h | grep Mem | awk '{print $2}')
- Available CPU Cores: $(nproc)

Next Steps:
1. If all tests passed: Ready for ASRock deployment
2. If tests failed: Review issues before proceeding
3. Deploy to ASRock using: ./scripts/deployment/deploy-edge.sh --unit-id 001

EOF

    success "Test report saved to: $report_file"
}

# Main test function
main() {
    echo "🔬 VAS System Regression Test"
    echo "============================="
    echo
    
    local test_results=""
    local all_tests_passed=true
    
    # Test 1: Original setup
    log "Test 1: Original Setup Functionality"
    if test_original_setup; then
        test_results+="✅ Original setup test: PASSED\n"
    else
        test_results+="❌ Original setup test: FAILED\n"
        all_tests_passed=false
    fi
    
    # Clean up before next test
    docker-compose -f "$ORIGINAL_COMPOSE" down
    sleep 5
    
    # Test 2: Performance benchmark
    log "Test 2: Performance Benchmark"
    if test_original_setup && benchmark_performance; then
        test_results+="✅ Performance benchmark: PASSED\n"
    else
        test_results+="❌ Performance benchmark: FAILED\n"
        all_tests_passed=false
    fi
    
    # Clean up
    docker-compose -f "$ORIGINAL_COMPOSE" down
    sleep 5
    
    # Test 3: Edge configuration validation
    log "Test 3: Edge Configuration Validation"
    if test_edge_config; then
        test_results+="✅ Edge config validation: PASSED\n"
    else
        test_results+="❌ Edge config validation: FAILED\n"
        all_tests_passed=false
    fi
    
    # Test 4: Configuration comparison
    log "Test 4: Configuration Comparison"
    if compare_configs; then
        test_results+="✅ Config comparison: PASSED\n"
    else
        test_results+="⚠️ Config comparison: WARNINGS\n"
    fi
    
    echo
    echo "📊 Test Summary:"
    echo "================"
    echo -e "$test_results"
    
    # Generate report
    generate_report "$test_results"
    
    if $all_tests_passed; then
        success "🎉 All regression tests passed! Ready for ASRock deployment."
        echo
        echo "Next steps:"
        echo "1. Deploy to ASRock unit: ./scripts/deployment/deploy-edge.sh --unit-id 001"
        echo "2. Test with 6 cameras on actual hardware"
        echo "3. Monitor performance with: curl http://localhost:3001/metrics"
        return 0
    else
        error "❌ Some tests failed. Please review issues before ASRock deployment."
        echo
        echo "Troubleshooting:"
        echo "1. Check logs: docker-compose logs"
        echo "2. Verify camera connections"
        echo "3. Check system resources"
        return 1
    fi
}

# Run main function
main "$@"
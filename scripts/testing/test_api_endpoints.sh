#!/bin/bash

# VAS WebRTC API Gateway Test Script
# Tests all API endpoints using curl

set -e

# Configuration
API_BASE_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin123"
AUTH_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test authentication
test_authentication() {
    log_info "Testing authentication..."
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/auth/login-json" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")
    
    if echo "$response" | grep -q "access_token"; then
        AUTH_TOKEN=$(echo "$response" | jq -r '.access_token')
        log_success "Authentication successful"
        log_info "Token: ${AUTH_TOKEN:0:20}..."
        return 0
    else
        log_error "Authentication failed: $response"
        return 1
    fi
}

# Test stream discovery
test_stream_discovery() {
    log_info "Testing stream discovery..."
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/streams/webrtc/streams" \
        -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$response" | grep -q "streams"; then
        local count=$(echo "$response" | jq -r '.total_count')
        log_success "Found $count streams"
        
        echo "$response" | jq -r '.streams[] | "  - Stream \(.stream_id): \(.name) (\(.status))"'
        return 0
    else
        log_error "Stream discovery failed: $response"
        return 1
    fi
}

# Test stream configuration
test_stream_config() {
    local stream_id="$1"
    log_info "Testing stream configuration for stream $stream_id..."
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/streams/webrtc/streams/$stream_id/config" \
        -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$response" | grep -q "janus_websocket_url"; then
        local ws_url=$(echo "$response" | jq -r '.janus_websocket_url')
        local mountpoint=$(echo "$response" | jq -r '.mountpoint_id')
        log_success "Stream $stream_id configuration retrieved"
        log_info "  WebSocket URL: $ws_url"
        log_info "  Mountpoint ID: $mountpoint"
        return 0
    else
        log_error "Stream $stream_id configuration failed: $response"
        return 1
    fi
}

# Test stream status
test_stream_status() {
    local stream_id="$1"
    log_info "Testing stream status for stream $stream_id..."
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/streams/webrtc/streams/$stream_id/status" \
        -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$response" | grep -q "status"; then
        local status=$(echo "$response" | jq -r '.status')
        local webrtc_ready=$(echo "$response" | jq -r '.webrtc_ready')
        log_success "Stream $stream_id status: $status (WebRTC Ready: $webrtc_ready)"
        return 0
    else
        log_error "Stream $stream_id status check failed: $response"
        return 1
    fi
}

# Test system status
test_system_status() {
    log_info "Testing system status..."
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/streams/webrtc/system/status" \
        -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$response" | grep -q "system_status"; then
        local system_status=$(echo "$response" | jq -r '.system_status')
        local total_streams=$(echo "$response" | jq -r '.total_streams')
        local active_streams=$(echo "$response" | jq -r '.active_streams')
        local janus_healthy=$(echo "$response" | jq -r '.janus_healthy')
        
        log_success "System status retrieved"
        log_info "  System Status: $system_status"
        log_info "  Total Streams: $total_streams"
        log_info "  Active Streams: $active_streams"
        log_info "  Janus Healthy: $janus_healthy"
        return 0
    else
        log_error "System status check failed: $response"
        return 1
    fi
}

# Test multiple concurrent requests
test_concurrent_requests() {
    log_info "Testing concurrent API requests..."
    
    local pids=()
    local results=()
    
    # Start multiple concurrent requests
    for i in {1..5}; do
        (
            local response=$(curl -s -X GET "$API_BASE_URL/api/streams/webrtc/streams" \
                -H "Authorization: Bearer $AUTH_TOKEN")
            if echo "$response" | grep -q "streams"; then
                echo "Request $i: SUCCESS"
            else
                echo "Request $i: FAILED"
            fi
        ) &
        pids+=($!)
    done
    
    # Wait for all requests to complete
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    log_success "Concurrent request test completed"
}

# Main test function
main() {
    echo "🚀 VAS WebRTC API Gateway Test"
    echo "================================"
    echo
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install it first."
        exit 1
    fi
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed."
        exit 1
    fi
    
    local test_results=()
    
    # Run tests
    echo "🔐 Testing Authentication..."
    if test_authentication; then
        test_results+=("✅ Authentication")
    else
        test_results+=("❌ Authentication")
        log_error "Cannot proceed without authentication"
        exit 1
    fi
    
    echo
    echo "📡 Testing Stream Discovery..."
    if test_stream_discovery; then
        test_results+=("✅ Stream Discovery")
    else
        test_results+=("❌ Stream Discovery")
    fi
    
    echo
    echo "🔧 Testing Stream Configuration..."
    if test_stream_config "1"; then
        test_results+=("✅ Stream Configuration")
    else
        test_results+=("❌ Stream Configuration")
    fi
    
    echo
    echo "📊 Testing Stream Status..."
    if test_stream_status "1"; then
        test_results+=("✅ Stream Status")
    else
        test_results+=("❌ Stream Status")
    fi
    
    echo
    echo "🏥 Testing System Status..."
    if test_system_status; then
        test_results+=("✅ System Status")
    else
        test_results+=("❌ System Status")
    fi
    
    echo
    echo "⚡ Testing Concurrent Requests..."
    test_concurrent_requests
    test_results+=("✅ Concurrent Requests")
    
    echo
    echo "📋 TEST SUMMARY"
    echo "==============="
    for result in "${test_results[@]}"; do
        echo "  $result"
    done
    
    echo
    log_success "WebRTC API Gateway test completed!"
    echo
    echo "🌐 To test the web interface:"
    echo "   python3 serve_test_page.py"
    echo "   Then open: http://localhost:8080/webrtc-api-test.html"
}

# Run main function
main "$@"

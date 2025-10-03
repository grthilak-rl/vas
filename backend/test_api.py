#!/usr/bin/env python3
"""
Comprehensive API Test Script for VAS Phase 1
Tests all endpoints and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages."""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW if status == "WARN" else Colors.BLUE
    print(f"{color}[{status}]{Colors.ENDC} {message}")

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None, expected_status: int = 200) -> Dict[str, Any]:
    """Test a single API endpoint."""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        success = response.status_code == expected_status
        print_status(f"{method} {endpoint} - Status: {response.status_code}", "PASS" if success else "FAIL")
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {"message": response.text}
        else:
            print(f"    Response: {response.text}")
            return {}
            
    except Exception as e:
        print_status(f"{method} {endpoint} - Error: {str(e)}", "FAIL")
        return {}

def main():
    """Run comprehensive API tests."""
    print(f"{Colors.BOLD}🚀 VAS Phase 1 API Test Suite{Colors.ENDC}")
    print(f"{Colors.BLUE}Testing API at: {BASE_URL}{Colors.ENDC}")
    print("=" * 60)
    
    # Test 1: Health Check (No Auth Required)
    print(f"\n{Colors.BOLD}1. Health Check{Colors.ENDC}")
    health_response = test_endpoint("GET", "/health")
    
    # Test 2: Root Endpoint (No Auth Required)
    print(f"\n{Colors.BOLD}2. Root Endpoint{Colors.ENDC}")
    root_response = test_endpoint("GET", "/")
    
    # Test 3: Authentication
    print(f"\n{Colors.BOLD}3. Authentication{Colors.ENDC}")
    
    # Test login with invalid credentials
    print_status("Testing login with invalid credentials", "INFO")
    test_endpoint("POST", "/auth/login-json", 
                 {"username": "wrong", "password": "wrong"}, 
                 expected_status=401)
    
    # Test login with valid credentials
    print_status("Testing login with valid credentials", "INFO")
    login_response = test_endpoint("POST", "/auth/login-json", 
                                  {"username": "admin", "password": "admin123"})
    
    if not login_response:
        print_status("Login failed - cannot continue with authenticated tests", "FAIL")
        return
    
    # Extract token
    token = login_response.get("access_token")
    if not token:
        print_status("No access token received", "FAIL")
        return
    
    auth_headers = {"Authorization": f"Bearer {token}"}
    print_status(f"Authentication successful - Token: {token[:20]}...", "PASS")
    
    # Test 4: Device Discovery
    print(f"\n{Colors.BOLD}4. Device Discovery{Colors.ENDC}")
    
    # Test discovery without auth
    print_status("Testing discovery without authentication", "INFO")
    test_endpoint("POST", "/discover", 
                 {"subnets": ["192.168.1.0/24"]}, 
                 expected_status=401)
    
    # Test discovery with auth
    print_status("Testing discovery with authentication", "INFO")
    discovery_response = test_endpoint("POST", "/discover", 
                                      {"subnets": ["192.168.1.0/24", "10.0.0.0/24"]}, 
                                      auth_headers)
    
    if discovery_response:
        task_id = discovery_response.get("task_id")
        print_status(f"Discovery task created: {task_id}", "PASS")
        
        # Wait a moment and check task status
        time.sleep(2)
        print_status("Checking discovery task status", "INFO")
        task_status = test_endpoint("GET", f"/discover/{task_id}", headers=auth_headers)
        
        # List all discovery tasks
        print_status("Listing all discovery tasks", "INFO")
        test_endpoint("GET", "/discover", headers=auth_headers)
    
    # Test 5: Device Management
    print(f"\n{Colors.BOLD}5. Device Management{Colors.ENDC}")
    
    # Test getting devices without auth
    print_status("Testing device list without authentication", "INFO")
    test_endpoint("GET", "/devices", expected_status=401)
    
    # Test getting devices with auth
    print_status("Testing device list with authentication", "INFO")
    devices_response = test_endpoint("GET", "/devices", headers=auth_headers)
    
    if devices_response and devices_response.get("devices"):
        device_id = devices_response["devices"][0]["id"]
        print_status(f"Found device: {device_id}", "PASS")
        
        # Test getting specific device
        print_status("Testing get specific device", "INFO")
        test_endpoint("GET", f"/devices/{device_id}", headers=auth_headers)
        
        # Test updating device
        print_status("Testing update device", "INFO")
        test_endpoint("PATCH", f"/devices/{device_id}", 
                     {"hostname": "test-updated.local"}, 
                     auth_headers)
        
        # Test device status check
        print_status("Testing device status check", "INFO")
        test_endpoint("GET", f"/devices/{device_id}/status", headers=auth_headers)
        
        # Test deleting device (will fail without admin role)
        print_status("Testing delete device (should fail for non-admin)", "INFO")
        test_endpoint("DELETE", f"/devices/{device_id}", headers=auth_headers, expected_status=403)
    else:
        print_status("No devices found - this is normal for a fresh installation", "WARN")
    
    # Test 6: RTSP Validation
    print(f"\n{Colors.BOLD}6. RTSP Validation{Colors.ENDC}")
    
    # Test validation without auth
    print_status("Testing validation without authentication", "INFO")
    test_endpoint("POST", "/devices/validate", 
                 {"ip_address": "192.168.1.100"}, 
                 expected_status=401)
    
    # Test validation with auth
    print_status("Testing validation with authentication", "INFO")
    validation_response = test_endpoint("POST", "/devices/validate", 
                                       {"ip_address": "192.168.1.100"}, 
                                       auth_headers)
    
    # Test validation with credentials
    print_status("Testing validation with credentials", "INFO")
    test_endpoint("POST", "/devices/validate", 
                 {"ip_address": "192.168.1.100", 
                  "username": "admin", 
                  "password": "password123"}, 
                 auth_headers)
    
    # Test 7: Error Handling
    print(f"\n{Colors.BOLD}7. Error Handling{Colors.ENDC}")
    
    # Test invalid device ID
    print_status("Testing invalid device ID", "INFO")
    test_endpoint("GET", "/devices/invalid-uuid", headers=auth_headers, expected_status=404)
    
    # Test invalid discovery request
    print_status("Testing invalid discovery request", "INFO")
    test_endpoint("POST", "/discover", {"subnets": []}, auth_headers, expected_status=422)
    
    # Test 8: API Documentation
    print(f"\n{Colors.BOLD}8. API Documentation{Colors.ENDC}")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print_status("Swagger UI is accessible", "PASS")
        else:
            print_status(f"Swagger UI returned status: {response.status_code}", "FAIL")
    except Exception as e:
        print_status(f"Swagger UI error: {str(e)}", "FAIL")
    
    try:
        response = requests.get(f"{BASE_URL}/redoc")
        if response.status_code == 200:
            print_status("ReDoc is accessible", "PASS")
        else:
            print_status(f"ReDoc returned status: {response.status_code}", "FAIL")
    except Exception as e:
        print_status(f"ReDoc error: {str(e)}", "FAIL")
    
    # Summary
    print(f"\n{Colors.BOLD}{'=' * 60}")
    print(f"🎉 API Test Suite Complete!")
    print(f"📖 API Documentation: {BASE_URL}/docs")
    print(f"🔧 Health Check: {BASE_URL}/api/health")
    print(f"{'=' * 60}{Colors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {str(e)}{Colors.ENDC}")
        sys.exit(1) 
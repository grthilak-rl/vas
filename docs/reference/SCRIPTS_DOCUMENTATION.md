# VAS System Scripts Documentation

## Overview

This document explains the purpose and functionality of the key automation scripts in the VAS (Video Analytics System) project.

## Scripts Overview

### deploy-edge.sh - ASRock Edge Deployment Script

**Primary Purpose:** Automated deployment of the VAS system optimized for ASRock iEP-7040E-024 edge computing units

**Target Environment:** Production ASRock hardware with Intel Core Ultra 7 255H processor and Intel Arc 140T GPU

**Key Functions:**

1. **Hardware-Optimized Deployment**
   - Deploys the 6-camera setup using `docker-compose.asrock-edge.yml`
   - Configures system for ASRock Intel Core Ultra 7 255H with Intel Arc 140T GPU
   - Sets up GPU access for AI inference (future YOLO integration)
   - Optimizes resource allocation for edge computing constraints

2. **Unit Management**
   - Assigns unique UNIT_ID (e.g., 001, 002, 050) to each ASRock device
   - Configures dynamic networking based on unit ID
   - Prepares for distributed edge computing architecture
   - Enables linear scalability across multiple units

3. **Configuration Management**
   - Replaces placeholder `${UNIT_ID}` in Janus and Nginx configs
   - Validates environment variables and system requirements
   - Creates necessary directories and backups
   - Ensures consistent configuration across deployments

4. **Service Orchestration**
   - Starts optimized services: `janus-edge`, `edge-api`, `vas-backend-edge`, `vas-frontend-edge`
   - Configures 6-camera streaming (172.16.16.122-127)
   - Sets up resource limits for CPU/GPU/memory
   - Manages Docker container lifecycle

5. **Health Monitoring and Validation**
   - Tests service health after deployment
   - Configures cameras via Edge API
   - Generates comprehensive deployment report
   - Validates system requirements before deployment

**Usage Examples:**
```bash
# Basic deployment with default settings
./scripts/deployment/deploy-edge.sh

# Deploy with specific unit ID and camera count
./scripts/deployment/deploy-edge.sh --unit-id 001 --cameras 6

# Update existing deployment
./scripts/deployment/deploy-edge.sh --unit-id 001 --update

# Get help
./scripts/deployment/deploy-edge.sh --help
```

**When to Use:** 
- Deploying to actual ASRock hardware with 6 cameras for production edge computing
- Setting up new edge computing units in distributed architecture
- Updating existing edge deployments
- Scaling to multiple ASRock units

---

### test-local-regression.sh - Regression Testing Script

**Primary Purpose:** Ensures that new ASRock edge changes don't break the existing 2-camera local setup

**Target Environment:** Local development environment with 2-camera setup

**Key Functions:**

1. **Backwards Compatibility Testing**
   - Tests original `docker-compose.yml` (2-camera setup) still works
   - Validates existing Janus streaming functionality
   - Checks HTML test page and React frontend accessibility
   - Ensures no regressions in core functionality

2. **Configuration Validation**
   - Validates syntax of `docker-compose.asrock-edge.yml`
   - Checks Janus edge configurations are properly formatted
   - Verifies resource limits and GPU mappings
   - Tests environment variable substitution

3. **Comparison Testing**
   - Compares original vs edge configurations
   - Identifies potential breaking changes
   - Ensures port mappings and networking remain compatible
   - Validates service dependencies

4. **Performance Benchmarking**
   - Placeholder for future performance tests
   - CPU/memory usage validation
   - Streaming latency measurements
   - Resource utilization monitoring

5. **Automated CI/CD Integration**
   - Exit codes for automated testing pipelines
   - Comprehensive logging and reporting
   - Cleanup functions for consistent test environment
   - JSON output format for integration

**Test Categories:**

1. **Original Setup Tests**
   - Docker Compose validation
   - Service startup verification
   - Janus Gateway functionality
   - Frontend accessibility
   - Camera stream availability

2. **Edge Configuration Tests**
   - YAML syntax validation
   - Resource limit verification
   - GPU mapping validation
   - Network configuration testing

3. **Compatibility Tests**
   - Port mapping comparison
   - Service name consistency
   - Volume mount validation
   - Environment variable compatibility

**Usage Examples:**
```bash
# Run all regression tests
./scripts/testing/test-local-regression.sh

# Run with verbose output
./scripts/testing/test-local-regression.sh --verbose

# Generate detailed report
./scripts/testing/test-local-regression.sh --report

# Quick syntax validation only
./scripts/testing/test-local-regression.sh --quick
```

**When to Use:**
- Before deploying edge changes to production
- After making modifications to Docker configurations
- In CI/CD pipelines for automated testing
- During development to catch regressions early
- Before releasing new versions

---

## Workflow Integration

### Development Workflow

1. **Make Changes to System**
   - Modify Docker configurations
   - Update service definitions
   - Change camera configurations

2. **Test for Regressions**
   ```bash
   ./scripts/testing/test-local-regression.sh
   ```
   - Ensures existing 2-camera setup still works
   - Validates configuration syntax
   - Checks for breaking changes

3. **Deploy to Production (if tests pass)**
   ```bash
   ./scripts/deployment/deploy-edge.sh --unit-id 001 --cameras 6
   ```
   - Deploys optimized configuration to ASRock hardware
   - Sets up 6-camera streaming
   - Configures edge computing services

### Production Deployment Workflow

**Single Unit Deployment:**
```bash
./scripts/deployment/deploy-edge.sh --unit-id 001
```

**Multiple Unit Deployment:**
```bash
# Deploy to multiple ASRock units
./scripts/deployment/deploy-edge.sh --unit-id 001  # First unit
./scripts/deployment/deploy-edge.sh --unit-id 002  # Second unit  
./scripts/deployment/deploy-edge.sh --unit-id 050  # 50th unit
```

**Update Existing Deployment:**
```bash
./scripts/deployment/deploy-edge.sh --unit-id 001 --update
```

---

## Configuration Files Used

### deploy-edge.sh Uses:
- `docker-compose.asrock-edge.yml` - Main edge configuration
- `janus/config/edge-janus.jcfg` - Optimized Janus configuration
- `janus/config/janus.plugin.streaming.edge.jcfg` - 6-camera streaming setup
- `nginx-edge.conf` - Edge-optimized Nginx configuration
- `edge-api/` - Edge API service configuration

### test-local-regression.sh Uses:
- `docker-compose.yml` - Original 2-camera configuration
- `docker-compose.asrock-edge.yml` - Edge configuration for validation
- `janus/config/janus.jcfg` - Original Janus configuration
- `test-camera-viewer.html` - HTML test interface

---

## Error Handling and Troubleshooting

### Common deploy-edge.sh Issues:

1. **Missing Docker/Docker Compose**
   - Error: "Docker is not installed"
   - Solution: Install Docker and Docker Compose

2. **Invalid UNIT_ID Format**
   - Error: "UNIT_ID must be 3 digits"
   - Solution: Use format like 001, 002, 050

3. **GPU Access Issues**
   - Error: "Intel Arc 140T not detected"
   - Solution: Install Intel GPU drivers

4. **Port Conflicts**
   - Error: "Port already in use"
   - Solution: Stop conflicting services

### Common test-local-regression.sh Issues:

1. **Service Startup Failures**
   - Error: "Container failed to start"
   - Solution: Check Docker logs, verify configurations

2. **Camera Connection Issues**
   - Error: "RTSP stream not accessible"
   - Solution: Verify camera IP addresses and credentials

3. **Configuration Syntax Errors**
   - Error: "Invalid YAML syntax"
   - Solution: Validate YAML files, check indentation

---

## Summary Comparison

| Script | Purpose | Target | Cameras | Environment | Use Case |
|--------|---------|--------|---------|-------------|----------|
| `deploy-edge.sh` | Production deployment | ASRock hardware | 6 cameras | Edge computing | Production scaling |
| `test-local-regression.sh` | Quality assurance | Local development | 2 cameras | Development | Prevent regressions |

Both scripts are essential for maintaining system reliability while scaling to distributed edge computing architecture. The regression testing script ensures stability during development, while the deployment script enables production-ready edge computing deployments.

"""
Edge API Service for ASRock Units
Manages local unit operations and reports to central dashboard
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import psutil
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
UNIT_ID = os.getenv("UNIT_ID", "001")
MAX_CAMERAS = int(os.getenv("MAX_CAMERAS", "6"))
JANUS_HTTP_URL = os.getenv("JANUS_HTTP_URL", "http://localhost:8088")
JANUS_ADMIN_URL = os.getenv("JANUS_ADMIN_URL", "http://localhost:7088/admin")
VAS_BACKEND_URL = os.getenv("VAS_BACKEND_URL", "http://vas-backend-edge:8000")
CENTRAL_DASHBOARD_URL = os.getenv("CENTRAL_DASHBOARD_URL", "")
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", "30"))  # seconds
INTEL_ARC_ENABLED = os.getenv("INTEL_ARC_ENABLED", "true").lower() == "true"

# Global state
reporting_task = None
unit_status = {
    "unit_id": UNIT_ID,
    "status": "initializing",
    "cameras": {},
    "performance": {},
    "last_update": None
}

# Pydantic models
class UnitStatus(BaseModel):
    unit_id: str
    status: str
    cameras: Dict[str, Dict]
    performance: Dict[str, float]
    last_update: Optional[str]

class CameraConfig(BaseModel):
    id: int
    rtsp_url: str
    description: str
    enabled: bool = True

class PerformanceMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    gpu_percent: Optional[float]
    camera_count: int
    active_streams: int
    janus_sessions: int

# Background reporting task
async def report_to_central():
    """Background task to report unit status to central dashboard"""
    if not CENTRAL_DASHBOARD_URL:
        logger.info("No central dashboard URL configured, skipping reporting")
        return
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Collect current metrics
                await update_unit_metrics()
                
                # Report to central dashboard
                response = await client.post(
                    f"{CENTRAL_DASHBOARD_URL}/api/units/{UNIT_ID}/status",
                    json=unit_status,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully reported to central dashboard")
                else:
                    logger.warning(f"Central dashboard returned status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Failed to report to central dashboard: {e}")
            
            await asyncio.sleep(REPORT_INTERVAL)

async def update_unit_metrics():
    """Update unit performance metrics and camera status"""
    global unit_status
    
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU metrics (Intel Arc)
        gpu_percent = None
        if INTEL_ARC_ENABLED:
            try:
                # Try to get Intel GPU usage (would need intel-gpu-tools)
                import subprocess
                result = subprocess.run(
                    ["intel_gpu_top", "-l", "1", "-s", "100"],
                    capture_output=True, text=True, timeout=5
                )
                # Parse intel_gpu_top output (simplified)
                if result.returncode == 0:
                    # This is a simplified parser - actual implementation would be more robust
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Render/3D' in line:
                            # Extract percentage (this is a simplified example)
                            gpu_percent = 0.0  # Placeholder
                            break
            except Exception:
                gpu_percent = None
        
        # Janus metrics
        janus_sessions = 0
        active_streams = 0
        try:
            async with httpx.AsyncClient() as client:
                # Get Janus info
                janus_response = await client.get(f"{JANUS_HTTP_URL}/janus/info", timeout=5)
                if janus_response.status_code == 200:
                    # Get session count from admin API
                    admin_response = await client.get(f"{JANUS_ADMIN_URL}/sessions", timeout=5)
                    if admin_response.status_code == 200:
                        admin_data = admin_response.json()
                        janus_sessions = len(admin_data.get("sessions", {}))
        except Exception as e:
            logger.warning(f"Failed to get Janus metrics: {e}")
        
        # Camera status
        camera_status = {}
        for i in range(1, MAX_CAMERAS + 1):
            camera_status[str(i)] = {
                "id": i,
                "status": "active",  # Simplified - would check actual RTSP status
                "stream_url": f"http://localhost:8088/janus/streaming/{i}",
                "last_seen": datetime.now(timezone.utc).isoformat()
            }
        
        # Update global status
        unit_status.update({
            "status": "online",
            "cameras": camera_status,
            "performance": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "gpu_percent": gpu_percent,
                "camera_count": MAX_CAMERAS,
                "active_streams": active_streams,
                "janus_sessions": janus_sessions,
                "uptime_seconds": psutil.boot_time(),
                "disk_usage_percent": psutil.disk_usage('/').percent
            },
            "last_update": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to update unit metrics: {e}")
        unit_status["status"] = "error"

# Startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global reporting_task
    logger.info(f"Starting Edge API for Unit {UNIT_ID}")
    
    # Start background reporting task
    reporting_task = asyncio.create_task(report_to_central())
    
    yield
    
    # Shutdown
    if reporting_task:
        reporting_task.cancel()
        try:
            await reporting_task
        except asyncio.CancelledError:
            pass
    logger.info("Edge API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="VAS Edge API",
    description=f"Edge API for ASRock Unit {UNIT_ID}",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "unit_id": UNIT_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "edge-api"
    }

# Unit status endpoint
@app.get("/status", response_model=UnitStatus)
async def get_unit_status():
    await update_unit_metrics()
    return unit_status

# Performance metrics endpoint
@app.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    await update_unit_metrics()
    return PerformanceMetrics(**unit_status["performance"])

# Camera management endpoints
@app.get("/cameras")
async def get_cameras():
    return unit_status.get("cameras", {})

@app.get("/cameras/{camera_id}")
async def get_camera(camera_id: str):
    cameras = unit_status.get("cameras", {})
    if camera_id not in cameras:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cameras[camera_id]

@app.post("/cameras/{camera_id}/restart")
async def restart_camera(camera_id: str):
    """Restart a specific camera stream"""
    if not camera_id.isdigit() or int(camera_id) < 1 or int(camera_id) > MAX_CAMERAS:
        raise HTTPException(status_code=400, detail="Invalid camera ID")
    
    try:
        # This would restart the specific stream in Janus
        # For now, return success
        return {
            "status": "success",
            "message": f"Camera {camera_id} restart initiated",
            "camera_id": camera_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart camera: {e}")

# Janus proxy endpoints
@app.get("/janus/info")
async def get_janus_info():
    """Proxy to Janus info endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{JANUS_HTTP_URL}/janus/info", timeout=10)
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Janus not available: {e}")

@app.get("/janus/sessions")
async def get_janus_sessions():
    """Get active Janus sessions"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{JANUS_ADMIN_URL}/sessions", timeout=10)
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Janus admin not available: {e}")

# System control endpoints
@app.post("/system/restart")
async def restart_system(background_tasks: BackgroundTasks):
    """Restart the entire edge unit (use with caution)"""
    logger.warning(f"System restart requested for unit {UNIT_ID}")
    
    def restart_containers():
        import subprocess
        try:
            subprocess.run(["docker-compose", "-f", "docker-compose.asrock-edge.yml", "restart"], 
                         check=True, timeout=60)
        except Exception as e:
            logger.error(f"Failed to restart containers: {e}")
    
    background_tasks.add_task(restart_containers)
    return {"status": "restart_initiated", "unit_id": UNIT_ID}

# Configuration endpoints
@app.get("/config")
async def get_unit_config():
    """Get current unit configuration"""
    return {
        "unit_id": UNIT_ID,
        "max_cameras": MAX_CAMERAS,
        "janus_url": JANUS_HTTP_URL,
        "central_dashboard": CENTRAL_DASHBOARD_URL,
        "intel_arc_enabled": INTEL_ARC_ENABLED,
        "report_interval": REPORT_INTERVAL
    }

# Future: AI inference endpoints (placeholder)
@app.get("/ai/status")
async def get_ai_status():
    """Get AI inference status (placeholder for future YOLO integration)"""
    return {
        "status": "not_implemented",
        "message": "AI inference will be implemented in future version",
        "intel_arc_available": INTEL_ARC_ENABLED
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)

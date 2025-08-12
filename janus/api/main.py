#!/usr/bin/env python3
"""
Janus Gateway API for VAS Integration
Fast, async API service for managing camera streams via Janus
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
import json
import uuid
from pydantic import BaseModel
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Janus Gateway API for VAS",
    description="RESTful API for managing IP camera streams via Janus WebRTC Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
JANUS_HTTP_URL = os.getenv("JANUS_HTTP_URL", "http://localhost:8088/janus")
JANUS_ADMIN_URL = os.getenv("JANUS_ADMIN_URL", "http://localhost:7088/admin")
JANUS_WS_URL = os.getenv("JANUS_WS_URL", "ws://localhost:8188/janus")

# In-memory store for camera configurations (use Redis/DB in production)
cameras_store: Dict[str, dict] = {}
active_sessions: Dict[str, dict] = {}

# Pydantic models
class CameraConfig(BaseModel):
    camera_id: str
    name: str
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    auth_method: str = "digest"
    description: Optional[str] = ""
    
class CameraResponse(BaseModel):
    camera_id: str
    name: str
    status: str
    stream_id: Optional[int] = None
    websocket_url: str
    
class StreamRequest(BaseModel):
    camera_id: str


class JanusClient:
    """Async Janus HTTP API Client"""
    
    def __init__(self):
        self.session = None
        
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def close(self):
        if self.session:
            await self.session.close()
            
    async def create_session(self) -> str:
        """Create a new Janus session"""
        session = await self.get_session()
        payload = {
            "janus": "create",
            "transaction": str(uuid.uuid4())
        }
        
        async with session.post(JANUS_HTTP_URL, json=payload) as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Failed to create Janus session")
            data = await response.json()
            # Handle both regular API and Admin API response formats
            if "data" in data and "id" in data["data"]:
                return str(data["data"]["id"])
            elif "session_id" in data:
                return str(data["session_id"])
            else:
                raise HTTPException(status_code=500, detail="Unexpected Janus response format")
            
    async def attach_plugin(self, session_id: str, plugin_name: str) -> str:
        """Attach to a Janus plugin"""
        session = await self.get_session()
        payload = {
            "janus": "attach",
            "plugin": plugin_name,
            "transaction": str(uuid.uuid4())
        }
        
        url = f"{JANUS_HTTP_URL}/{session_id}"
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Failed to attach plugin")
            data = await response.json()
            return str(data["data"]["id"])
            
    async def send_message(self, session_id: str, handle_id: str, message: dict):
        """Send message to Janus plugin"""
        session = await self.get_session()
        payload = {
            "janus": "message",
            "transaction": str(uuid.uuid4()),
            "body": message
        }
        
        url = f"{JANUS_HTTP_URL}/{session_id}/{handle_id}"
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Failed to send message")
            return await response.json()
            
    async def destroy_session(self, session_id: str):
        """Destroy Janus session"""
        session = await self.get_session()
        payload = {
            "janus": "destroy",
            "transaction": str(uuid.uuid4())
        }
        
        url = f"{JANUS_HTTP_URL}/{session_id}"
        async with session.post(url, json=payload) as response:
            return response.status == 200

# Global Janus client
janus_client = JanusClient()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Janus Gateway API for VAS")
    logger.info(f"Janus HTTP URL: {JANUS_HTTP_URL}")
    logger.info(f"Janus WebSocket URL: {JANUS_WS_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    await janus_client.close()
    logger.info("Janus Gateway API shutdown complete")

@app.get("/")
async def root():
    return {
        "service": "Janus Gateway API for VAS",
        "version": "1.0.0",
        "status": "running",
        "janus_url": JANUS_HTTP_URL,
        "websocket_url": JANUS_WS_URL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for VAS monitoring"""
    try:
        # Test Janus Admin API connectivity
        session = await janus_client.get_session()
        payload = {
            "janus": "list_sessions",
            "transaction": str(uuid.uuid4())
        }
        
        async with session.post(JANUS_HTTP_URL, json=payload) as response:
            if response.status != 200:
                raise HTTPException(status_code=503, detail="Failed to connect to Janus")
            data = await response.json()
            
            return {
                "status": "healthy",
                "janus_connectivity": "ok",
                "janus_response": data.get("janus", "unknown"),
                "active_cameras": len(cameras_store),
                "active_sessions": len(active_sessions)
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Janus connectivity failed: {str(e)}")

@app.post("/cameras", response_model=CameraResponse)
async def add_camera(camera: CameraConfig):
    """Add a new camera to the streaming service"""
    logger.info(f"Adding camera: {camera.camera_id}")
    
    if camera.camera_id in cameras_store:
        raise HTTPException(status_code=409, detail="Camera already exists")
    
    try:
        # Create Janus session for this camera
        session_id = await janus_client.create_session()
        handle_id = await janus_client.attach_plugin(session_id, "janus.plugin.streaming")
        
        # Generate unique stream ID
        stream_id = len(cameras_store) + 1
        
        # Create streaming mountpoint
        create_message = {
            "request": "create",
            "type": "rtsp",
            "id": stream_id,
            "description": camera.description or camera.name,
            "is_private": False,
            "video": True,
            "audio": False,
            "url": camera.rtsp_url,
            "rtsp_user": camera.username,
            "rtsp_pwd": camera.password,
            "rtsp_authmethod": camera.auth_method,
            "videopt": 96,
            "videocodec": "h264"
        }
        
        response = await janus_client.send_message(session_id, handle_id, create_message)
        
        # Store camera configuration
        cameras_store[camera.camera_id] = {
            "config": camera.dict(),
            "session_id": session_id,
            "handle_id": handle_id,
            "stream_id": stream_id,
            "status": "active"
        }
        
        logger.info(f"Camera {camera.camera_id} added successfully with stream ID {stream_id}")
        
        return CameraResponse(
            camera_id=camera.camera_id,
            name=camera.name,
            status="active",
            stream_id=stream_id,
            websocket_url=JANUS_WS_URL
        )
        
    except Exception as e:
        logger.error(f"Failed to add camera {camera.camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add camera: {str(e)}")

@app.get("/cameras", response_model=List[CameraResponse])
async def list_cameras():
    """Get list of all configured cameras"""
    cameras = []
    for camera_id, camera_data in cameras_store.items():
        config = camera_data["config"]
        cameras.append(CameraResponse(
            camera_id=camera_id,
            name=config["name"],
            status=camera_data["status"],
            stream_id=camera_data.get("stream_id"),
            websocket_url=JANUS_WS_URL
        ))
    return cameras

@app.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    """Get details for a specific camera"""
    if camera_id not in cameras_store:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    camera_data = cameras_store[camera_id]
    config = camera_data["config"]
    
    return CameraResponse(
        camera_id=camera_id,
        name=config["name"],
        status=camera_data["status"],
        stream_id=camera_data.get("stream_id"),
        websocket_url=JANUS_WS_URL
    )

@app.get("/cameras/{camera_id}/stream")
async def get_stream_info(camera_id: str):
    """Get WebRTC streaming information for VAS frontend"""
    if camera_id not in cameras_store:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    camera_data = cameras_store[camera_id]
    
    return {
        "camera_id": camera_id,
        "stream_id": camera_data["stream_id"],
        "janus_url": JANUS_WS_URL,
        "plugin": "janus.plugin.streaming",
        "stream_info": {
            "id": camera_data["stream_id"],
            "type": "rtsp",
            "description": camera_data["config"]["description"]
        }
    }

@app.post("/cameras/{camera_id}/restart")
async def restart_camera(camera_id: str):
    """Restart a camera stream"""
    if camera_id not in cameras_store:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    try:
        camera_data = cameras_store[camera_id]
        
        # Destroy current stream
        destroy_message = {
            "request": "destroy",
            "id": camera_data["stream_id"]
        }
        
        await janus_client.send_message(
            camera_data["session_id"], 
            camera_data["handle_id"], 
            destroy_message
        )
        
        # Recreate stream with same configuration
        config = camera_data["config"]
        create_message = {
            "request": "create",
            "type": "rtsp",
            "id": camera_data["stream_id"],
            "description": config["description"],
            "is_private": False,
            "video": True,
            "audio": False,
            "url": config["rtsp_url"],
            "rtsp_user": config["username"],
            "rtsp_pwd": config["password"],
            "rtsp_authmethod": config["auth_method"],
            "videopt": 96,
            "videocodec": "h264"
        }
        
        await janus_client.send_message(
            camera_data["session_id"], 
            camera_data["handle_id"], 
            create_message
        )
        
        logger.info(f"Camera {camera_id} restarted successfully")
        return {"message": f"Camera {camera_id} restarted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to restart camera {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restart camera: {str(e)}")

@app.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: str):
    """Remove a camera from the streaming service"""
    if camera_id not in cameras_store:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    try:
        camera_data = cameras_store[camera_id]
        
        # Destroy stream
        destroy_message = {
            "request": "destroy",
            "id": camera_data["stream_id"]
        }
        
        await janus_client.send_message(
            camera_data["session_id"], 
            camera_data["handle_id"], 
            destroy_message
        )
        
        # Destroy session
        await janus_client.destroy_session(camera_data["session_id"])
        
        # Remove from store
        del cameras_store[camera_id]
        
        logger.info(f"Camera {camera_id} removed successfully")
        return {"message": f"Camera {camera_id} removed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to remove camera {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove camera: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
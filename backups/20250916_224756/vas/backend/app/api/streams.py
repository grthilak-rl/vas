"""
Stream Management API
Handles WebRTC stream operations via Janus Gateway
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import asyncio

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models import Device, DeviceStatus as DeviceModelStatus
from app.schemas import StreamResponse, StreamStatus, JanusMountpoint
from app.services.janus_service import janus_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("/", response_model=List[StreamResponse])
async def list_streams(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List all available streams with their proxy mountpoint status"""
    try:
        devices = db.query(Device).all()
        # Eagerly load data and close the session
        device_data_list = [d.to_dict() for d in devices]
    finally:
        db.close()

    try:
        mountpoints = await janus_service.list_mountpoints()
        mountpoint_map = {mp["id"]: mp for mp in mountpoints}
        
        streams = []
        for device_data in device_data_list:
            # This logic assumes a fixed mapping from device ID to a mountpoint ID
            # In a real system, you might have a more dynamic way to look this up
            proxy_mountpoint_id = janus_service.get_proxy_mountpoint_for_device_sync(str(device_data["id"]))
            
            mountpoint_info = None
            stream_status = StreamStatus.INACTIVE
            webrtc_url = None

            if proxy_mountpoint_id and proxy_mountpoint_id in mountpoint_map:
                mountpoint_info = mountpoint_map[proxy_mountpoint_id]
                # Check if the stream is active based on Janus's report
                if mountpoint_info.get("streaming"):
                    stream_status = StreamStatus.ACTIVE
                    webrtc_url = janus_service.get_webrtc_url()
            
            # The device dictionary has its own 'status' (ONLINE/OFFLINE).
            # We must remove it to avoid a keyword argument conflict with the stream's status.
            device_data.pop("status", None)

            stream = StreamResponse(
                **device_data,
                status=stream_status,
                mountpoint_info=JanusMountpoint(**mountpoint_info) if mountpoint_info else None,
                webrtc_url=webrtc_url
            )
            streams.append(stream)
        
        return streams
        
    except Exception as e:
        logger.error(f"Error listing streams: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list streams due to an internal error."
        )


@router.post("/{device_id}/start", response_model=StreamResponse)
async def start_stream(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Start streaming for a device by activating its proxy mountpoint."""
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        
        if device.status != DeviceModelStatus.ONLINE:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Device is not online. Current status: {device.status.value}")

        device_data = device.to_dict()
        device_data.pop("status", None)
        proxy_mountpoint_id = janus_service.get_proxy_mountpoint_for_device_sync(device_id)

    finally:
        db.close()

    if not proxy_mountpoint_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No proxy mountpoint configured for this device.")

    try:
        is_active = await janus_service.is_proxy_mountpoint_active(proxy_mountpoint_id)
        if not is_active:
            logger.warning(f"Attempted to start stream for device {device_id}, but its FFmpeg proxy mountpoint ({proxy_mountpoint_id}) is not active in Janus.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Camera stream is not available. Check FFmpeg proxy and camera connectivity."
            )
        
        mountpoint_info = await janus_service.get_mountpoint_info(proxy_mountpoint_id)
        
        return StreamResponse(
            **device_data,
            status=StreamStatus.ACTIVE,
            mountpoint_info=mountpoint_info,
            webrtc_url=janus_service.get_webrtc_url()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting stream for device {device_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start stream due to an internal error.")


@router.post("/{device_id}/stop", response_model=StreamResponse)
async def stop_stream(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Stops a stream. In the current proxy model, this is a no-op
    as streams are always 'on' in the background via FFmpeg.
    This endpoint confirms the mountpoint is inactive.
    """
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        device_data = device.to_dict()
        device_data.pop("status", None)
    finally:
        db.close()

    # With the proxy model, we don't 'stop' the stream, we just confirm its status.
    # The stream is always running via ffmpeg. A client just disconnects.
    return StreamResponse(**device_data, status=StreamStatus.INACTIVE, mountpoint_info=None)


@router.get("/{device_id}/status", response_model=StreamResponse)
async def get_stream_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get the current status of a stream."""
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        device_data = device.to_dict()
        device_data.pop("status", None)
        proxy_mountpoint_id = janus_service.get_proxy_mountpoint_for_device_sync(str(device.id))
    finally:
        db.close()

    try:
        if not proxy_mountpoint_id:
            return StreamResponse(**device_data, status=StreamStatus.INACTIVE)

        mountpoint_info = await janus_service.get_mountpoint_info(proxy_mountpoint_id)
        
        if mountpoint_info and mountpoint_info.get("streaming"):
            return StreamResponse(
                **device_data,
                status=StreamStatus.ACTIVE,
                mountpoint_info=JanusMountpoint(**mountpoint_info),
                webrtc_url=janus_service.get_webrtc_url()
            )
        else:
            return StreamResponse(
                **device_data,
                status=StreamStatus.INACTIVE,
                mountpoint_info=JanusMountpoint(**mountpoint_info) if mountpoint_info else None
            )
            
    except Exception as e:
        logger.error(f"Error getting stream status for {device_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get stream status.")


@router.get("/janus/mountpoints")
async def list_janus_mountpoints(
    current_user = Depends(get_current_user)
):
    """List all Janus mountpoints (for debugging)"""
    try:
        mountpoints = await janus_service.list_mountpoints()
        return {"mountpoints": mountpoints}
        
    except Exception as e:
        logger.error(f"Error listing Janus mountpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Janus mountpoints"
        )


@router.get("/janus/health")
async def janus_health_check():
    """Check Janus Gateway health"""
    try:
        is_healthy = await janus_service.health_check()
        return {
            "janus_healthy": is_healthy,
            "status": "healthy" if is_healthy else "unhealthy"
        }
        
    except Exception as e:
        logger.error(f"Janus health check failed: {e}")
        return {
            "janus_healthy": False,
            "status": "error",
            "error": str(e)
        } 
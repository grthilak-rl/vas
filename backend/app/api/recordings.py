"""
Recording API
Handles recording management and playback endpoints for Live DVR functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os

from app.database import get_db
from app.api.dependencies import get_current_user, get_current_admin_user
from app.models import Device, DeviceStatus
from app.services.live_dvr_service import get_live_dvr_service
from app.schemas import (
    RecordingStartResponse,
    RecordingStopResponse,
    RecordingStatusResponse,
    RecordingSegmentListResponse,
    RecordingTimelineResponse,
    StorageUsageResponse,
    CleanupResponse,
    AllRecordingStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("/{device_id}/start", response_model=RecordingStartResponse)
async def start_recording(
    device_id: UUID,
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Start continuous recording for a device
    
    Args:
        device_id: Device UUID to start recording for
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message with recording status
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Check if device is online
        if device.status != DeviceStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device is not online. Current status: {device.status.value}"
            )
        
        # Check if already recording
        if get_live_dvr_service().get_recording_status(str(device_id)):
            return {
                "message": "Recording already active for this device",
                "device_id": str(device_id),
                "is_recording": True
            }
        
        # Start recording
        success = await get_live_dvr_service().start_recording(device, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start recording. Check device connectivity and RTSP stream."
            )
        
        return {
            "message": "Recording started successfully",
            "device_id": str(device_id),
            "device_name": device.name,
            "is_recording": True,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting recording for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while starting recording"
        )


@router.post("/{device_id}/stop", response_model=RecordingStopResponse)
async def stop_recording(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Stop continuous recording for a device
    
    Args:
        device_id: Device UUID to stop recording for
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message with recording status
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Check if recording is active
        if not get_live_dvr_service().get_recording_status(str(device_id)):
            return {
                "message": "No active recording for this device",
                "device_id": str(device_id),
                "is_recording": False
            }
        
        # Stop recording
        success = await get_live_dvr_service().stop_recording(str(device_id), db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop recording"
            )
        
        return {
            "message": "Recording stopped successfully",
            "device_id": str(device_id),
            "device_name": device.name,
            "is_recording": False,
            "stopped_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping recording for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while stopping recording"
        )


@router.get("/{device_id}/status", response_model=RecordingStatusResponse)
async def get_recording_status(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get recording status for a device
    
    Args:
        device_id: Device UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Recording status information
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get recording status
        is_recording = get_live_dvr_service().get_recording_status(str(device_id))
        
        # Get storage usage for this device
        storage_usage = get_live_dvr_service().get_storage_usage()
        device_storage = storage_usage.get(str(device_id), 0)
        
        return {
            "device_id": str(device_id),
            "device_name": device.name,
            "is_recording": is_recording,
            "device_status": device.status.value,
            "storage_bytes": device_storage,
            "storage_mb": round(device_storage / (1024 * 1024), 2),
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recording status for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting recording status"
        )


@router.get("/{device_id}/segments", response_model=RecordingSegmentListResponse)
async def get_recording_segments(
    device_id: UUID,
    start_time: Optional[datetime] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time filter (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of segments to return"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get recording segments for a device within a time range
    
    Args:
        device_id: Device UUID
        start_time: Optional start time filter
        end_time: Optional end time filter
        limit: Maximum number of segments to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of recording segments
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get recording segments
        segments = await get_live_dvr_service().get_recording_segments(
            str(device_id), 
            start_time=start_time, 
            end_time=end_time, 
            db=db
        )
        
        # Limit results
        segments = segments[:limit]
        
        return {
            "device_id": str(device_id),
            "device_name": device.name,
            "segments": segments,
            "total_segments": len(segments),
            "time_range": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recording segments for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting recording segments"
        )


@router.get("/{device_id}/timeline", response_model=RecordingTimelineResponse)
async def get_recording_timeline(
    device_id: UUID,
    hours: int = Query(24, ge=1, le=168, description="Number of hours to include in timeline"),
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Get recording timeline for a device showing available segments
    
    Args:
        device_id: Device UUID
        hours: Number of hours to include in timeline
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Timeline data with available segments
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get recording segments
        segments = await get_live_dvr_service().get_recording_segments(
            str(device_id),
            start_time=start_time,
            end_time=end_time,
            db=db
        )
        
        # Process segments into timeline format
        timeline_data = []
        for segment in segments:
            timeline_data.append({
                "id": segment["id"],
                "start_time": segment["start_timestamp"],
                "end_time": segment["end_timestamp"],
                "duration_seconds": segment["duration_seconds"],
                "file_size_bytes": segment["file_size_bytes"],
                "file_size_mb": round(segment["file_size_bytes"] / (1024 * 1024), 2),
                "playback_url": f"/api/recordings/{device_id}/segment/{segment['id']}/play"
            })
        
        return {
            "device_id": str(device_id),
            "device_name": device.name,
            "timeline_hours": hours,
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "segments": timeline_data,
            "total_segments": len(timeline_data),
            "is_recording": get_live_dvr_service().get_recording_status(str(device_id))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recording timeline for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting recording timeline"
        )


@router.get("/{device_id}/segment/{segment_id}/play")
async def play_recording_segment(
    device_id: UUID,
    segment_id: UUID,
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Stream a recording segment for playback
    
    Args:
        device_id: Device UUID
        segment_id: Segment UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Video stream response
    """
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get segment information from database
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT segment_file_path, start_timestamp, end_timestamp, duration_seconds
            FROM recording_segments 
            WHERE id = :segment_id AND device_id = :device_id
        """), {
            'segment_id': str(segment_id),
            'device_id': str(device_id)
        })
        
        segment_data = result.fetchone()
        if not segment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording segment not found"
            )
        
        file_path = Path(segment_data.segment_file_path)
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording file not found on disk"
            )
        
        # Return video file
        return Response(
            content=file_path.read_bytes(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename={file_path.name}",
                "X-Segment-Start": segment_data.start_timestamp.isoformat(),
                "X-Segment-End": segment_data.end_timestamp.isoformat(),
                "X-Segment-Duration": str(segment_data.duration_seconds)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error playing recording segment {segment_id} for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while playing recording segment"
        )


@router.get("/storage/usage", response_model=StorageUsageResponse)
async def get_storage_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Get storage usage statistics for recordings
    
    Args:
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Storage usage information
    """
    try:
        storage_usage = get_live_dvr_service().get_storage_usage()
        
        # Convert bytes to MB and GB
        total_bytes = storage_usage.get('total', 0)
        total_mb = round(total_bytes / (1024 * 1024), 2)
        total_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
        
        # Get device-specific usage
        device_usage = []
        for device_id, bytes_used in storage_usage.items():
            if device_id != 'total':
                device = db.query(Device).filter(Device.id == device_id).first()
                if device:
                    device_usage.append({
                        "device_id": device_id,
                        "device_name": device.name,
                        "bytes_used": bytes_used,
                        "mb_used": round(bytes_used / (1024 * 1024), 2),
                        "gb_used": round(bytes_used / (1024 * 1024 * 1024), 2)
                    })
        
        return {
            "total_storage": {
                "bytes": total_bytes,
                "mb": total_mb,
                "gb": total_gb
            },
            "device_usage": device_usage,
            "recordings_directory": str(get_live_dvr_service().recordings_dir),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting storage usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting storage usage"
        )


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_expired_segments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Manually trigger cleanup of expired recording segments
    
    Args:
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Cleanup results
    """
    try:
        cleaned_count = await get_live_dvr_service().cleanup_expired_segments(db)
        
        return {
            "message": f"Cleanup completed successfully",
            "segments_cleaned": cleaned_count,
            "cleanup_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during cleanup"
        )


@router.get("/status/all", response_model=AllRecordingStatusResponse)
async def get_all_recording_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get recording status for all devices
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Recording status for all devices
    """
    try:
        # Get all devices
        devices = db.query(Device).all()
        
        status_data = []
        for device in devices:
            is_recording = get_live_dvr_service().get_recording_status(str(device.id))
            storage_usage = get_live_dvr_service().get_storage_usage()
            device_storage = storage_usage.get(str(device.id), 0)
            
            status_data.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "device_status": device.status.value,
                "is_recording": is_recording,
                "storage_bytes": device_storage,
                "storage_mb": round(device_storage / (1024 * 1024), 2)
            })
        
        return {
            "devices": status_data,
            "total_devices": len(devices),
            "recording_devices": sum(1 for d in status_data if d["is_recording"]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all recording status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting recording status"
        )


@router.get("/cleanup/status")
async def get_cleanup_status(
    current_user=Depends(get_current_user)
):
    """
    Get cleanup service status and storage information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Cleanup service status and storage metrics
    """
    try:
        status = get_live_dvr_service().get_cleanup_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting cleanup status"
        )


@router.post("/cleanup/force")
async def force_cleanup(
    current_user=Depends(get_current_admin_user)
):
    """
    Manually trigger cleanup process
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Cleanup results and status
    """
    try:
        result = get_live_dvr_service().force_cleanup()
        return result
        
    except Exception as e:
        logger.error(f"Error during forced cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during forced cleanup"
        )


@router.get("/cleanup/history")
async def get_cleanup_history(
    limit: int = Query(50, ge=1, le=1000, description="Number of cleanup events to return"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Get cleanup history and statistics
    
    Args:
        limit: Maximum number of cleanup events to return
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Cleanup history and statistics
    """
    try:
        from sqlalchemy import text
        
        # Get recent cleanup statistics from recording_status table
        result = db.execute(text("""
            SELECT 
                device_id,
                total_segments,
                total_size_bytes,
                updated_at
            FROM recording_status 
            ORDER BY updated_at DESC
            LIMIT :limit
        """), {'limit': limit})
        
        cleanup_history = []
        for row in result.fetchall():
            cleanup_history.append({
                "device_id": str(row.device_id),
                "total_segments": row.total_segments,
                "total_size_bytes": row.total_size_bytes,
                "total_size_mb": round(row.total_size_bytes / (1024 * 1024), 2),
                "last_updated": row.updated_at.isoformat() if row.updated_at else None
            })
        
        # Get overall statistics
        total_result = db.execute(text("""
            SELECT 
                COUNT(*) as total_segments,
                SUM(file_size_bytes) as total_size_bytes
            FROM recording_segments
        """))
        
        total_stats = total_result.fetchone()
        
        return {
            "cleanup_history": cleanup_history,
            "total_segments": total_stats.total_segments or 0,
            "total_size_bytes": total_stats.total_size_bytes or 0,
            "total_size_mb": round((total_stats.total_size_bytes or 0) / (1024 * 1024), 2),
            "cleanup_service_status": get_live_dvr_service().get_cleanup_status(),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cleanup history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting cleanup history"
        )
